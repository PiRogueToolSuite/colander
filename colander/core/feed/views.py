from colander_data_converter.base.models import ColanderFeed
from django.http import JsonResponse
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_201_CREATED
from rest_framework.viewsets import GenericViewSet

from colander.core.feed.importer import FeedImporter
from colander.core.models import Case
from colander.core.rest.middlewares import CanContributeToCase


class FeedViewSet(GenericViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated, CanContributeToCase]

    # @action(detail=False, methods=["POST"])
    # def render_template(self, request):
    #     template_id = self.request.data.pop("template_id")
    #     case_id = self.request.data.pop("case_id")
    #     case = Case.objects.get(pk=case_id)
    #     feed_data = self.request.data.pop("feed")
    #
    #     try:
    #         feed = ColanderFeed.load(feed_data, reset_ids=True)
    #         feed_importer = FeedImporter(case, feed)
    #         feed_importer.import_feed()
    #     except Exception as e:
    #         return JsonResponse(
    #             {"status": "failed", "message": str(e)},
    #             status=HTTP_400_BAD_REQUEST
    #         )
    #     return JsonResponse(
    #         {"status": "success", "message": "Feed successfully imported"},
    #         status=HTTP_201_CREATED
    #     )

    @action(detail=False, methods=["POST"])
    def import_feed(self, request):
        case_id = self.request.data.pop("case_id")
        case = Case.objects.get(pk=case_id)
        feed_data = self.request.data.pop("feed")

        try:
            feed = ColanderFeed.load(feed_data, reset_ids=True)
            feed_importer = FeedImporter(case, feed)
            feed_importer.import_feed()
        except Exception as e:
            return JsonResponse(
                {"status": "failed", "message": str(e)},
                status=HTTP_400_BAD_REQUEST
            )
        return JsonResponse(
            {"status": "success", "message": "Feed successfully imported"},
            status=HTTP_201_CREATED
        )

    @action(detail=False, methods=["POST"])
    def import_entities(self, request):
        case_id = self.request.data.pop("case_id")
        case = Case.objects.get(pk=case_id)
        entities = self.request.data.pop("entities")

        feed_data = {
            "entities": {str(entity.get("id")): entity for entity in entities},
            "cases": {},
            "relations": {}
        }

        try:
            feed = ColanderFeed.load(feed_data, reset_ids=True)
            feed_importer = FeedImporter(case, feed)
            feed_importer.import_feed()
        except Exception as e:
            return JsonResponse(
                {"status": "failed", "message": str(e)},
                status=HTTP_400_BAD_REQUEST
            )

        return JsonResponse(
            {"status": "success", "message": f"{len(entities)} entities successfully imported"},
            status=HTTP_201_CREATED
        )
