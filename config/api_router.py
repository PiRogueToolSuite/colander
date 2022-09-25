from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from colander.core.api.views import ExperimentViewSet, NetworkDumpViewSet, EvidenceViewSet
from colander.users.api.views import UserViewSet

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register("users", UserViewSet)

router.register("experiment", ExperimentViewSet)
router.register("network_dump", NetworkDumpViewSet)
router.register("evidence", EvidenceViewSet)


app_name = "api"
urlpatterns = router.urls
