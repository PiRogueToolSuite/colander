from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from colander.core.models import SubGraph


@login_required
def graph_base_view(request):
    ctx = {
        'pinned_subgraphs': SubGraph.get_pinned(user=request.user, case=request.contextual_case).order_by('created_at')
    }
    return render(request, 'pages/graph/base.html', context=ctx)
