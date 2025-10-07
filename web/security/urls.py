from django.urls import path
from . import views

app_name = 'security'

urlpatterns = [
    path('whitelisted-ips/', views.whitelisted_ips, name='whitelisted_ips'),
    path('blocked-ips/', views.blocked_ips, name='blocked_ips'),
    path('remove-whitelist/<int:ip_id>/', views.remove_whitelist, name='remove_whitelist'),
    path('unblock-ip/<str:ip>/', views.unblock_ip, name='unblock_ip'),
    path('whitelist-ip/<str:ip>/', views.whitelist_ip, name='whitelist_ip'),
]
