import base64
import json

from django.contrib.auth.decorators import login_required
from django.core.files import File
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from colander.core.graph.serializers import GraphCaseSerializer, SubGraphCaseSerializer
from colander.core.models import Case, SubGraph


@login_required
def case_graph(request, pk):
    if request.method == 'GET':
        case = get_object_or_404(Case, id=pk)
        if not case.can_contribute(request.user):
            return JsonResponse(status_code=401, data={})
        s = GraphCaseSerializer(instance=case)
        return JsonResponse(data=s.data)

    elif request.method == 'PATCH':
        case = get_object_or_404(Case, id=pk)

        if not case.can_contribute(request.user):
            return JsonResponse(status_code=401, data={})

        data = json.loads(request.body)
        if 'thumbnail' in data:
            del data['thumbnail']
        # all this data are considered overrides
        case.overrides = data
        case.save()

        return JsonResponse(data={'success': True})

    else:
        return JsonResponse(status_code=405, data={})


@login_required
def case_subgraph(request, pk):
    if request.method == 'GET':
        subgraph = get_object_or_404(SubGraph, id=pk)
        if not subgraph.case.can_contribute(request.user):
            return JsonResponse(status_code=401, data={})
        s = SubGraphCaseSerializer(instance=subgraph)
        return JsonResponse(data=s.data)

    elif request.method == 'PATCH':
        subgraph = get_object_or_404(SubGraph, id=pk)

        if not subgraph.case.can_contribute(request.user):
            return JsonResponse(status_code=401, data={})

        data = json.loads(request.body)

        if 'thumbnail' in data:
            thumbnailB64 = data.pop('thumbnail')
            thumbnail_buff = base64.b64decode(thumbnailB64)
            subgraph.thumbnail = ContentFile(thumbnail_buff, name='thumbnail.png')

        subgraph.overrides = data
        subgraph.save()

        return JsonResponse(data={'success': True})

    else:
        return JsonResponse(status_code=405, data={})
