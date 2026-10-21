from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from finances.models import Category, PaymentMethod, PaymentType
from datetime import timedelta
from dateutil.relativedelta import relativedelta

User = get_user_model()


class Subscription(models.Model):
    """
    Suscripción recurrente.

    Puede ser infinita (end_date vacía). Los Expense futuros no se crean
    "para siempre": se materializa un horizonte móvil (por defecto 12 meses,
    alineado al gráfico de estimaciones) y el comando
    ``create_subscription_expenses`` lo va extendiendo.
    """

    FREQUENCY_CHOICES = [
        ('weekly', 'Semanal'),
        ('monthly', 'Mensual'),
        ('quarterly', 'Trimestral'),
        ('biannual', 'Semestral'),
        ('annual', 'Anual'),
    ]

    STATUS_CHOICES = [
        ('active', 'Activa'),
        ('paused', 'Pausada'),
        ('cancelled', 'Cancelada'),
        ('expired', 'Expirada'),
    ]

    # Horizonte de gastos materializados (NO es un límite de vida de la suscripción)
    EXPENSE_HORIZON_MONTHS = 12

    name = models.CharField(max_length=200, verbose_name='Nombre')
    description = models.TextField(blank=True, null=True, verbose_name='Descripción')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Monto')
    currency = models.CharField(
        max_length=3,
        choices=[('ARS', 'Pesos (ARS)'), ('USD', 'Dólares (USD)')],
        default='ARS',
        verbose_name='Moneda',
        help_text='Si es USD, el gasto en pesos se estima con la cotización blue y se fija el día de pago.',
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Usuario')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='Categoría')
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE, verbose_name='Método de Pago')
    payment_type = models.ForeignKey(PaymentType, on_delete=models.CASCADE, verbose_name='Tipo de Pago')

    frequency = models.CharField(
        max_length=20, choices=FREQUENCY_CHOICES, default='monthly', verbose_name='Frecuencia'
    )
    start_date = models.DateField(verbose_name='Fecha de Inicio')
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de Fin',
        help_text='Vacío = sin caducidad (suscripción infinita).',
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name='Estado')
    auto_create_expense = models.BooleanField(default=True, verbose_name='Crear Gastos Automáticamente')
    reminder_days = models.IntegerField(default=7, verbose_name='Días de Recordatorio')

    last_renewal_date = models.DateField(null=True, blank=True, verbose_name='Última Renovación')
    next_renewal_validation = models.DateField(null=True, blank=True, verbose_name='Próxima Validación de Renovación')
    renewal_reminder_sent = models.BooleanField(default=False, verbose_name='Recordatorio de Renovación Enviado')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Última Actualización')

    class Meta:
        verbose_name = 'Suscripción'
        verbose_name_plural = 'Suscripciones'
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user']),
            models.Index(fields=['status']),
            models.Index(fields=['category']),
            models.Index(fields=['payment_method']),
            models.Index(fields=['payment_type']),
        ]

    def __str__(self):
        return f"{self.name} - ${self.amount} ({self.get_frequency_display()})"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        previous = None
        if not is_new:
                previous = (
                Subscription.objects.filter(pk=self.pk)
                .values(
                    'status', 'amount', 'currency', 'frequency', 'start_date',
                    'end_date', 'auto_create_expense',
                )
                .first()
            )

        update_fields = kwargs.get('update_fields')
        super().save(*args, **kwargs)

        # Si el caller limitó update_fields a campos que no afectan gastos, no tocar expenses
        if update_fields is not None:
            relevant = {
                'status', 'amount', 'currency', 'frequency', 'start_date', 'end_date',
                'auto_create_expense', 'name', 'category', 'payment_method', 'payment_type', 'user',
            }
            if not relevant.intersection(update_fields):
                return

        rebuild = False
        if previous:
            rebuild = (
                previous['amount'] != self.amount
                or previous.get('currency', 'ARS') != self.currency
                or previous['frequency'] != self.frequency
                or previous['start_date'] != self.start_date
            )

        self.sync_expenses(rebuild_future=rebuild or is_new)

    def is_active(self):
        """Activa y sin caducar (end_date vacía = infinita)."""
        if self.status != 'active':
            return False
        if self.end_date and self.end_date < timezone.now().date():
            return False
        return True

    def _add_period(self, current_date):
        """Avanzar una fecha según la frecuencia."""
        if self.frequency == 'weekly':
            return current_date + timedelta(weeks=1)
        if self.frequency == 'monthly':
            return current_date + relativedelta(months=1)
        if self.frequency == 'quarterly':
            return current_date + relativedelta(months=3)
        if self.frequency == 'biannual':
            return current_date + relativedelta(months=6)
        if self.frequency == 'annual':
            return current_date + relativedelta(years=1)
        return current_date + relativedelta(months=1)

    def clear_future_expenses(self):
        """Eliminar gastos futuros ligados a esta suscripción (no toca el pasado)."""
        from finances.models import Expense

        today = timezone.now().date()
        return Expense.objects.filter(subscription=self, date__gt=today).delete()[0]

    def delete(self, *args, **kwargs):
        # Expense.subscription usa SET_NULL: sin esto, los futuros quedan huérfanos
        # y se duplican al recrear la suscripción.
        self.clear_future_expenses()
        return super().delete(*args, **kwargs)

    def sync_expenses(self, rebuild_future=False, horizon_months=None):
        """
        Sincroniza gastos materializados con el estado actual.

        - Pausada / cancelada / sin auto_create: borra futuros.
        - Activa: asegura gastos desde hoy hasta horizonte (12 meses por defecto).
        """
        if not self.auto_create_expense or not self.is_active():
            return self.clear_future_expenses()
        return self.ensure_expenses(
            horizon_months=horizon_months or self.EXPENSE_HORIZON_MONTHS,
            rebuild_future=rebuild_future,
        )

    def _period_to_expense_date(self, period_date):
        """
        Fecha del Expense según método de pago.

        - Crédito (TC): primer lunes (>= día 7) del mes siguiente al período
          (misma lógica que las cuotas en /finances/).
        - Efectivo / débito / transferencia: se respeta la fecha del período.
        """
        from finances.dates import get_card_payment_monday

        method_name = getattr(self.payment_method, 'name', '') or ''
        if method_name == 'credito':
            next_month = period_date + relativedelta(months=1)
            return get_card_payment_monday(next_month.year, next_month.month)
        return period_date

    def _resolve_ars_amount(self, rate=None):
        """
        Devuelve (amount_ars, amount_usd, cotizacion, fx_locked_hint).

        USD: estimado con cotización actual (no fijado todavía).
        ARS: monto directo, sin FX.
        """
        from decimal import Decimal
        from core.fx import get_dollar_quotation, usd_to_ars

        if self.currency == 'USD':
            if rate is None:
                rate = get_dollar_quotation()
            ars = usd_to_ars(self.amount, rate=rate)
            if ars is None:
                # Sin cotización no inventamos pesos: usar 0 y dejar sin lock
                return Decimal('0.00'), Decimal(str(self.amount)), None, False
            return ars, Decimal(str(self.amount)), Decimal(str(rate)), False
        return Decimal(str(self.amount)), None, None, True

    def ensure_expenses(self, horizon_months=None, rebuild_future=False):
        """
        Crea los Expense faltantes hasta ``today + horizon_months``.

        La suscripción puede ser infinita; solo se materializa el horizonte.
        Respeta ``end_date`` si está definida.
        """
        from finances.models import Expense

        horizon_months = horizon_months or self.EXPENSE_HORIZON_MONTHS
        today = timezone.now().date()

        if rebuild_future:
            self.clear_future_expenses()

        if not self.auto_create_expense or not self.is_active():
            return 0

        horizon_end = today + relativedelta(months=horizon_months)
        if self.end_date:
            horizon_end = min(horizon_end, self.end_date)

        if horizon_end < today:
            return 0

        rate = None
        if self.currency == 'USD':
            from core.fx import get_dollar_quotation
            rate = get_dollar_quotation()

        created = 0
        current = self.start_date
        payment_horizon = horizon_end + relativedelta(months=2)
        max_iterations = 800
        for _ in range(max_iterations):
            if self.end_date and current > self.end_date:
                break
            if current > horizon_end + relativedelta(months=2):
                break

            expense_date = self._period_to_expense_date(current)
            if expense_date >= today and expense_date <= payment_horizon:
                exists = Expense.objects.filter(
                    subscription=self, date=expense_date
                ).exists()
                if not exists:
                    amount_ars, amount_usd, cotiz, locked = self._resolve_ars_amount(rate=rate)
                    if self.currency == 'USD':
                        locked = bool(cotiz) and expense_date <= today
                    else:
                        locked = True

                    Expense.objects.create(
                        user=self.user,
                        date=expense_date,
                        name=self.name,
                        amount=amount_ars,
                        category=self.category,
                        payment_method=self.payment_method,
                        payment_type=self.payment_type,
                        description=f"Suscripción: {self.name}",
                        is_credit=False,
                        subscription=self,
                        amount_usd=amount_usd,
                        cotizacion_dolar=cotiz,
                        fx_locked=locked,
                    )
                    created += 1

            nxt = self._add_period(current)
            if nxt <= current:
                break
            current = nxt

        return created

    @classmethod
    def refresh_usd_estimates_and_lock(cls):
        """
        - Gastos USD de suscripción aún no fijados y fecha > hoy: refrescar estimado.
        - Gastos USD con fecha <= hoy: fijar cotización del día y ARS.
        """
        from decimal import Decimal
        from finances.models import Expense
        from core.fx import get_dollar_quotation, usd_to_ars

        today = timezone.now().date()
        rate = get_dollar_quotation()
        if rate is None:
            return 0, 0

        updated_estimates = 0
        locked = 0

        pending = Expense.objects.filter(
            subscription__isnull=False,
            amount_usd__isnull=False,
            fx_locked=False,
        )
        for expense in pending.select_related('subscription'):
            ars = usd_to_ars(expense.amount_usd, rate=rate)
            if ars is None:
                continue
            expense.amount = ars
            expense.cotizacion_dolar = Decimal(str(rate))
            if expense.date <= today:
                expense.fx_locked = True
                locked += 1
            else:
                updated_estimates += 1
            expense.save(update_fields=['amount', 'cotizacion_dolar', 'fx_locked', 'updated_at'])

        return updated_estimates, locked

    @classmethod
    def extend_all_active_expenses(cls, horizon_months=None):
        """Extiende horizonte + refresca/fija FX de suscripciones USD."""
        horizon_months = horizon_months or cls.EXPENSE_HORIZON_MONTHS
        total_created = 0
        processed = 0
        for subscription in cls.objects.filter(status='active', auto_create_expense=True):
            if not subscription.is_active():
                continue
            processed += 1
            total_created += subscription.ensure_expenses(horizon_months=horizon_months)
        est, locked = cls.refresh_usd_estimates_and_lock()
        return processed, total_created, est, locked

    def amount_ars_today(self, rate=None):
        """Monto en pesos al día de hoy (USD convertido con blue actual)."""
        from decimal import Decimal
        from core.fx import usd_to_ars

        if self.currency != 'USD':
            return Decimal(str(self.amount))
        ars = usd_to_ars(self.amount, rate=rate)
        return ars if ars is not None else Decimal('0.00')

    def monthly_ars_equivalent(self, rate=None):
        """Equivalente mensual en ARS (para totales del listado)."""
        from decimal import Decimal

        ars = self.amount_ars_today(rate=rate)
        if self.frequency == 'weekly':
            return (ars * Decimal('4.33')).quantize(Decimal('0.01'))
        if self.frequency == 'monthly':
            return ars
        if self.frequency == 'quarterly':
            return (ars / Decimal('3')).quantize(Decimal('0.01'))
        if self.frequency == 'biannual':
            return (ars / Decimal('6')).quantize(Decimal('0.01'))
        if self.frequency == 'annual':
            return (ars / Decimal('12')).quantize(Decimal('0.01'))
        return ars

    @property
    def next_payment_date(self):
        return self.get_next_payment_date()

    def get_next_payment_date(self):
        """Próxima fecha de cobro efectiva (>= hoy), ya convertida a fecha TC si aplica."""
        if not self.is_active():
            return None

        today = timezone.now().date()
        period = self.start_date
        for _ in range(800):
            expense_date = self._period_to_expense_date(period)
            if expense_date >= today:
                if self.end_date and period > self.end_date:
                    return None
                return expense_date
            nxt = self._add_period(period)
            if nxt <= period:
                return None
            period = nxt
        return None

    def advance_payment(self):
        """Avanzar al siguiente pago (actualiza start_date al próximo vencimiento)."""
        next_date = self.get_next_payment_date()
        if next_date:
            self.start_date = next_date
            self.last_renewal_date = timezone.now().date()
            self.save(update_fields=['start_date', 'last_renewal_date', 'updated_at'])
            return True
        return False

    def is_due_soon(self):
        if not self.is_active():
            return False
        next_date = self.get_next_payment_date()
        if next_date:
            return (next_date - timezone.now().date()).days <= self.reminder_days
        return False

    def is_overdue(self):
        if not self.is_active():
            return False
        next_date = self.get_next_payment_date()
        if next_date:
            return next_date < timezone.now().date()
        return False

    def get_total_paid(self):
        from finances.models import Expense

        return Expense.objects.filter(
            subscription=self,
            date__lte=timezone.now().date(),
        ).aggregate(total=models.Sum('amount'))['total'] or 0

    def get_remaining_payments(self):
        """Pagos restantes hasta end_date. None si la suscripción es infinita."""
        if not self.end_date:
            return None

        total_payments = 0
        current_date = timezone.now().date()
        for _ in range(800):
            if current_date > self.end_date:
                break
            current_date = self._add_period(current_date)
            total_payments += 1
        return total_payments

    def needs_renewal_validation(self):
        if not self.next_renewal_validation:
            return False
        return timezone.now().date() >= self.next_renewal_validation

    def mark_renewal_reminder_sent(self):
        self.renewal_reminder_sent = True
        self.save(update_fields=['renewal_reminder_sent', 'updated_at'])
