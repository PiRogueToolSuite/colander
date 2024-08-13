from django.conf import settings
from django.urls import path
from rest_framework.routers import DefaultRouter, SimpleRouter

from colander.core.rest.views import DatasetViewSet, EntityRelationViewSet, EntityViewSet, import_entity_from_threatr
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
