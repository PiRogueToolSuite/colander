from rest_framework import mixins
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from colander.core.graph.serializers import GraphRelationSerializer
from colander.core.models import Case, EntityRelation


class EntityRelationViewSet(mixins.CreateModelMixin,
                            mixins.UpdateModelMixin,
                            mixins.DestroyModelMixin,
                            GenericViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = GraphRelationSerializer

    def get_queryset(self):
        cases = self.request.user.all_my_cases
        return EntityRelation.objects.filter(case__in=cases)

    def perform_create(self, serializer):
        return serializer.save(
            owner=self.request.user,
            case=Case.objects.get(pk=self.request.session.get('active_case'))
        )
