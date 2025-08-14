from django.urls import path
from . import views

app_name = 'forecasts'

urlpatterns = [
    # Dashboard de estimaciones
    path('', views.forecast_dashboard, name='forecast_dashboard'),
    
    # CRUD de estimaciones
    path('expense-forecast/create/', views.expense_forecast_create, name='expense_forecast_create'),
    path('expense-forecast/<int:pk>/', views.expense_forecast_detail, name='expense_forecast_detail'),
    path('expense-forecast/<int:pk>/edit/', views.expense_forecast_edit, name='expense_forecast_edit'),
    path('expense-forecast/<int:pk>/delete/', views.expense_forecast_delete, name='expense_forecast_delete'),
    
    # Vistas especiales
    path('monthly/', views.monthly_forecasts, name='monthly_forecasts'),
    path('generate/', views.generate_forecasts, name='generate_forecasts'),
    path('generate-suggestions/', views.generate_suggestions, name='generate_suggestions'),
    path('expense-forecast/<int:pk>/activate/', views.activate_suggestion, name='activate_suggestion'),
]
