from django.urls import path
from . import views

app_name = 'subscriptions'

urlpatterns = [
    # Lista de suscripciones
    path('', views.subscription_list, name='subscription_list'),
    
    # CRUD de suscripciones
    path('create/', views.subscription_create, name='subscription_create'),
    path('<int:subscription_id>/', views.subscription_detail, name='subscription_detail'),
    path('<int:subscription_id>/edit/', views.subscription_edit, name='subscription_edit'),
    path('<int:subscription_id>/delete/', views.subscription_delete, name='subscription_delete'),
    
    # Acciones especiales
    path('<int:subscription_id>/advance/', views.subscription_advance, name='subscription_advance'),
    path('<int:subscription_id>/toggle-status/', views.subscription_toggle_status, name='subscription_toggle_status'),
    
    # Dashboard de suscripciones
    path('dashboard/', views.subscription_dashboard, name='dashboard'),
]
