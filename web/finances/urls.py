from django.urls import path
from . import views

app_name = 'finances'

urlpatterns = [
    # Dashboard financiero
    path('dashboard/', views.dashboard_finances, name='dashboard'),
    
    # CRUD de gastos
    path('', views.expense_list, name='expense_list'),
    path('create/', views.expense_create, name='expense_create'),
    path('<int:expense_id>/', views.expense_detail, name='expense_detail'),
    path('<int:expense_id>/edit/', views.expense_edit, name='expense_edit'),
    path('<int:expense_id>/delete/', views.expense_delete, name='expense_delete'),
    
    # Exportación
    path('export/', views.export_expenses, name='export_expenses'),
]
