from django.urls import path
from . import views

app_name = 'finances'

urlpatterns = [
    path('', views.expense_list, name='expense_list'),
    path('create/', views.expense_create, name='expense_create'),
    path('<int:pk>/', views.expense_detail, name='expense_detail'),
    path('<int:pk>/edit/', views.expense_edit, name='expense_edit'),
    path('<int:pk>/delete/', views.expense_delete, name='expense_delete'),
    path('dashboard/', views.dashboard_finances, name='dashboard_finances'),
    path('export/', views.export_expenses, name='export_expenses'),
    path('get-payment-types/', views.get_payment_types, name='get_payment_types'),
]
