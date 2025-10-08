from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'whitelist', views.WhitelistedIPViewSet)
router.register(r'blocked', views.BlockedIPViewSet)

urlpatterns = router.urls