from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from colander.core.api.views import ApiDeviceViewSet, ApiDeviceTypeViewSet, ApiArtifactViewSet
from colander.users.api.views import UserViewSet

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register("users", UserViewSet)
router.register("artifacts", ApiArtifactViewSet, basename='artifacts')
router.register("devices", ApiDeviceViewSet, basename='devices')
router.register("device_types", ApiDeviceTypeViewSet, basename='device_types')

app_name = "api"
urlpatterns = router.urls
