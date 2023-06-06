from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from colander.core.graph.serializers import GraphCaseSerializer
from colander.core.models import Case


@login_required
def case_graph(request, pk):
    if request.method == 'GET':
        case = get_object_or_404(Case, id=pk)
        if not case.can_contribute(request.user):
            return JsonResponse(status_code=401, data={})
        s = GraphCaseSerializer(instance=case)
        return JsonResponse(data=s.data)
    else:
        return JsonResponse(status_code=405, data={})
