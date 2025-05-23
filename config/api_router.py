from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from colander.core.api.views import (
    ApiArtifactTypeViewSet,
    ApiArtifactViewSet,
    ApiCaseViewSet,
    ApiDeviceTypeViewSet,
    ApiDeviceViewSet,
    ApiDroppedFileViewSet,
    ApiObservableTypeViewSet,
    ApiObservableViewSet,
    ApiPiRogueExperimentViewSet,
    ApiRelationViewSet,
    ApiTeamViewSet,
    ApiUploadRequestViewSet,
)

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

# Do not expose User API for now
# router.register("users", UserViewSet)
router.register("cases", ApiCaseViewSet, basename='cases')
router.register("artifacts", ApiArtifactViewSet, basename='artifacts')
router.register("artifact_types", ApiArtifactTypeViewSet, basename='artifacts_types')
router.register("upload_requests", ApiUploadRequestViewSet, basename='upload_requests')
router.register("devices", ApiDeviceViewSet, basename='devices')
router.register("device_types", ApiDeviceTypeViewSet, basename='device_types')
router.register("drops", ApiDroppedFileViewSet, basename='drops')
router.register("observables", ApiObservableViewSet, basename='observables')
router.register("observable_types", ApiObservableTypeViewSet, basename='observable_types')
router.register("pirogue_experiments", ApiPiRogueExperimentViewSet, basename='pirogue_experiments')
router.register("relations", ApiRelationViewSet, basename='relations')
router.register("teams", ApiTeamViewSet, basename='teams')

app_name = "api"
urlpatterns = router.urls
