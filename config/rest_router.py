from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from colander.core.api.views import ApiCaseViewSet, ApiDeviceViewSet, ApiDeviceTypeViewSet, ApiArtifactViewSet, \
    ApiArtifactTypeViewSet, ApiUploadRequestViewSet, ApiPiRogueExperimentViewSet
from colander.core.rest.views import EntityRelationViewSet

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register("entity_relation", EntityRelationViewSet, basename="entity_relation")

app_name = "rest"
urlpatterns = router.urls
