import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum, Q
from django.http import JsonResponse
from django.utils import timezone
from rest_framework import viewsets, permissions
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from .models import Income, IncomeCategory, IncomeSource
from .forms import IncomeForm, IncomeFilterForm
from .serializers import IncomeSerializer, IncomeCategorySerializer, IncomeSourceSerializer
from accounts.models import CustomUser

logger = logging.getLogger(__name__)


@login_required
def income_list(request):
    """List view for income entries with filters and pagination"""
    form = IncomeFilterForm(request.GET)

    incomes = Income.objects.all()

    # Apply filters
    if form.is_valid():
        if form.cleaned_data.get('date_from'):
            incomes = incomes.filter(date__gte=form.cleaned_data['date_from'])
        if form.cleaned_data.get('date_to'):
            incomes = incomes.filter(date__lte=form.cleaned_data['date_to'])

        if form.cleaned_data.get('category'):
            incomes = incomes.filter(category=form.cleaned_data['category'])

        if form.cleaned_data.get('source'):
            incomes = incomes.filter(source=form.cleaned_data['source'])

        if form.cleaned_data.get('user'):
            incomes = incomes.filter(user=form.cleaned_data['user'])

        if form.cleaned_data.get('is_recurring') is not None:
            is_recurring_value = form.cleaned_data['is_recurring']
            if is_recurring_value == 'True':
                incomes = incomes.filter(is_recurring=True)
            elif is_recurring_value == 'False':
                incomes = incomes.filter(is_recurring=False)

        if form.cleaned_data.get('min_amount'):
            incomes = incomes.filter(amount__gte=form.cleaned_data['min_amount'])

        if form.cleaned_data.get('max_amount'):
            incomes = incomes.filter(amount__lte=form.cleaned_data['max_amount'])

        if form.cleaned_data.get('search'):
            search_term = form.cleaned_data['search']
            incomes = incomes.filter(description__icontains=search_term)

    # Ordering
    sort_order = form.cleaned_data.get('sort_order', 'newest')
    if sort_order == 'oldest':
        incomes = incomes.order_by('date', 'id')
    else:
        incomes = incomes.order_by('-date', '-id')

    # Default to current month if no filters
    if not any([form.cleaned_data.get('date_from'), form.cleaned_data.get('date_to'),
                form.cleaned_data.get('category'), form.cleaned_data.get('source'),
                form.cleaned_data.get('user'),
                form.cleaned_data.get('is_recurring'), form.cleaned_data.get('min_amount'),
                form.cleaned_data.get('max_amount'), form.cleaned_data.get('search')]):

        today = timezone.now().date()
        first_day = today.replace(day=1)
        if today.month == 12:
            last_day = today.replace(year=today.year + 1, month=1, day=1) - timezone.timedelta(days=1)
        else:
            last_day = today.replace(month=today.month + 1, day=1) - timezone.timedelta(days=1)

        incomes = incomes.filter(date__range=[first_day, last_day])
        period_display = f"{first_day.strftime('%B %Y')}"
    else:
        if form.cleaned_data.get('date_from') and form.cleaned_data.get('date_to'):
            period_display = f"From {form.cleaned_data['date_from'].strftime('%d/%m/%Y')} to {form.cleaned_data['date_to'].strftime('%d/%m/%Y')}"
        elif form.cleaned_data.get('date_from'):
            period_display = f"From {form.cleaned_data['date_from'].strftime('%d/%m/%Y')}"
        elif form.cleaned_data.get('date_to'):
            period_display = f"To {form.cleaned_data['date_to'].strftime('%d/%m/%Y')}"
        else:
            period_display = "All periods"

    total_amount = incomes.aggregate(total=Sum('amount'))['total'] or 0
    total_dollars = incomes.aggregate(total=Sum('en_dolares'))['total'] or 0

    user_filter_display = None
    if form.cleaned_data.get('user'):
        user_filter_display = form.cleaned_data['user'].username

    paginator = Paginator(incomes, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'incomes': page_obj,
        'form': form,
        'total_amount': total_amount,
        'total_dollars': total_dollars,
        'period_display': period_display,
        'user_filter_display': user_filter_display,
    }

    return render(request, 'income/income_list.html', context)


@login_required
def income_create(request):
    """Create a new income entry"""
    if request.method == 'POST':
        form = IncomeForm(request.POST)
        if form.is_valid():
            income = form.save(commit=False)
            income.user = request.user
            income.save()
            messages.success(request, 'Income entry created successfully.')
            return redirect('income:income_list')
    else:
        form = IncomeForm()

    context = {
        'form': form,
        'title': 'New Income'
    }

    return render(request, 'income/income_form.html', context)


@login_required
def income_edit(request, pk):
    """Edit an existing income entry"""
    income = get_object_or_404(Income, pk=pk)

    if request.method == 'POST':
        form = IncomeForm(request.POST, instance=income)
        if form.is_valid():
            form.save()
            messages.success(request, 'Income entry updated successfully.')
            return redirect('income:income_list')
    else:
        form = IncomeForm(instance=income)

    context = {
        'form': form,
        'income': income,
        'title': 'Edit Income'
    }

    return render(request, 'income/income_form.html', context)


@login_required
def income_delete(request, pk):
    """Delete an income entry"""
    income = get_object_or_404(Income, pk=pk)

    if request.method == 'POST':
        income.delete()
        messages.success(request, 'Income entry deleted successfully.')
        return redirect('income:income_list')

    context = {
        'income': income
    }

    logger.info(f"Attempting to render template: income/income_delete.html for income delete view")
    return render(request, 'income/income_delete.html', context)


@login_required
def income_detail(request, pk):
    """View income entry details"""
    income = get_object_or_404(Income, pk=pk)

    context = {
        'income': income
    }

    return render(request, 'income/income_detail.html', context)


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user


class IncomeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Income model with filtering and user ownership permissions.
    """
    serializer_class = IncomeSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['user', 'date', 'category', 'source', 'is_recurring']
    ordering_fields = ['date', 'amount', 'created_at']
    ordering = ['-date']

    def get_queryset(self):
        queryset = Income.objects.all()
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        else:
            queryset = queryset.filter(user=self.request.user)

        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')

        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class IncomeCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for IncomeCategory model.
    """
    queryset = IncomeCategory.objects.all()
    serializer_class = IncomeCategorySerializer
    permission_classes = [permissions.IsAuthenticated]


class IncomeSourceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for IncomeSource model.
    """
    queryset = IncomeSource.objects.all()
    serializer_class = IncomeSourceSerializer
    permission_classes = [permissions.IsAuthenticated]

