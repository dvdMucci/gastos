from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import dashboard # Importa el dashboard de tu app 'accounts'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard, name='dashboard'), # Redirección de la raíz al dashboard
    path('dashboard/', dashboard, name='dashboard'),

    path('accounts/', include('accounts.urls')), # Incluye las URLs de la aplicación 'accounts'
    path('finances/', include('finances.urls')), # Incluye las URLs de la aplicación 'finances'
    path('income/', include('income.urls')), # Incluye las URLs de la aplicación 'income'
    path('subscriptions/', include('subscriptions.urls')), # Incluye las URLs de la aplicación 'subscriptions'
    path('forecasts/', include('forecasts.urls')), # Incluye las URLs de la aplicación 'forecasts'

    # API authentication
    path('api-auth/', include('rest_framework.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)