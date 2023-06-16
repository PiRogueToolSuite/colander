from rest_framework import mixins
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from colander.core.graph.serializers import GraphRelationSerializer
from colander.core.models import Case


class EntityRelationViewSet(mixins.CreateModelMixin,
                            mixins.UpdateModelMixin,
                            GenericViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = GraphRelationSerializer

    def perform_create(self, serializer):
        print('perform create', '!!!!!', self.request.session.get('active_case'))
        print('perform create', serializer.validated_data)

        return serializer.save(
            owner=self.request.user,
            case=Case.objects.get(pk=self.request.session.get('active_case'))
        )
