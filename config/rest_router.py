from django.conf import settings
from django.urls import path
from rest_framework.routers import DefaultRouter, SimpleRouter

from colander.core.feed.views import FeedImportViewSet
from colander.core.rest.views import DatasetViewSet, EntityRelationViewSet, EntityViewSet, \
    import_entity_from_threatr, DroppedFileViewSet, CaseViewSet, ArtifactTypeViewSet, \
    SubGraphViewSet
from colander.core.views.cached_files_view import CachedFileApiView
from colander.core.views.views import entity_exists, overall_search, entity_types

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register('artifact_types', ArtifactTypeViewSet, basename='artifact_types')
router.register("cases", CaseViewSet, basename="cases")
router.register("dataset", DatasetViewSet, basename="dataset")
router.register("drops", DroppedFileViewSet, basename="drops")
router.register("entity", EntityViewSet, basename="entity")
router.register("feed", FeedImportViewSet, basename="feed")
router.register("entity_relation", EntityRelationViewSet, basename="entity_relation")
router.register("subgraph", SubGraphViewSet, basename="subgraph")

app_name = "rest"
urlpatterns = router.urls

urlpatterns += [
    path("entity/suggest", entity_exists, name="entity_exists_view"),
    path("entity/types", entity_types, name="entity_types_view"),
    path("search", overall_search, name="overall_search"),
    path("threatr_entity", import_entity_from_threatr, name="import_entity_from_threatr_view"),
    path("cached", CachedFileApiView.as_view(), name="cached_files"),
    path("cached/<uuid:pk>", CachedFileApiView.as_view(), name="cached_file_detail"),
]
