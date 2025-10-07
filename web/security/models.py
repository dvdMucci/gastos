from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class WhitelistedIP(models.Model):
    """
    Modelo para IPs en lista blanca que no serán bloqueadas por el middleware de seguridad
    """
    ip = models.GenericIPAddressField(
        unique=True,
        verbose_name='Dirección IP',
        help_text='Dirección IP a incluir en lista blanca'
    )
    added_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Agregado por',
        related_name='whitelisted_ips'
    )
    date_added = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de agregado'
    )
    reason = models.TextField(
        blank=True,
        verbose_name='Razón',
        help_text='Razón por la cual se agregó esta IP a la lista blanca'
    )

    class Meta:
        verbose_name = 'IP en Lista Blanca'
        verbose_name_plural = 'IPs en Lista Blanca'
        ordering = ['-date_added']

    def __str__(self):
        return f"{self.ip} - {self.reason or 'Sin razón especificada'}"
