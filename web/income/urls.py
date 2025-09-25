from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'income'

# API Router
router = DefaultRouter()
router.register(r'incomes', views.IncomeViewSet, basename='income')
router.register(r'categories', views.IncomeCategoryViewSet, basename='income-category')
router.register(r'sources', views.IncomeSourceViewSet, basename='income-source')

urlpatterns = [
    path('', views.income_list, name='income_list'),
    path('create/', views.income_create, name='income_create'),
    path('<int:pk>/', views.income_detail, name='income_detail'),
    path('<int:pk>/edit/', views.income_edit, name='income_edit'),
    path('<int:pk>/delete/', views.income_delete, name='income_delete'),

    # API URLs
    path('api/', include(router.urls)),
]