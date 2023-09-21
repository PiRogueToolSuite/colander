from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from colander.core.views.views import get_active_case


@login_required
def graph_base_view(request):
    active_case = get_active_case(request)
    ctx = {}
    return render(request, 'pages/graph/base.html', context=ctx)
