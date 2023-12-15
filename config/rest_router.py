from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter
from django.urls import path

from colander.core.api.views import ApiCaseViewSet, ApiDeviceViewSet, ApiDeviceTypeViewSet, ApiArtifactViewSet, \
    ApiArtifactTypeViewSet, ApiUploadRequestViewSet, ApiPiRogueExperimentViewSet
from colander.core.rest.views import EntityRelationViewSet, import_entity_from_threatr, EntityViewSet, DatasetViewSet
from colander.core.views.views import entity_exists, overall_search

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register("entity_relation", EntityRelationViewSet, basename="entity_relation")
router.register("entity", EntityViewSet, basename="entity")
router.register("dataset", DatasetViewSet, basename="dataset")


app_name = "rest"
urlpatterns = router.urls

urlpatterns += [
    path("threatr_entity", import_entity_from_threatr, name="import_entity_from_threatr_view"),
    path("entity/suggest", entity_exists, name="entity_exists_view"),
    path("search", overall_search, name="overall_search"),
]
