import json

from colander_data_converter.base.models import ColanderFeed
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from colander.core.feed.importer import FeedImporter


@login_required
def import_view(request):
    active_case = request.contextual_case
    if not active_case:
        return redirect('case_create_view')

    if request.method == 'POST':
        raw = request.POST.get('content', '')
        raw_content = json.loads(raw)
        feed = ColanderFeed.load(raw_content, reset_ids=True)
        feed_importer = FeedImporter(active_case, feed)
        feed_importer.import_feed()

    ctx = {
        'active_case': active_case,
    }
    return render(request, 'pages/import/base.html', context=ctx)


@login_required
def import_misp_view(request):
    active_case = request.contextual_case
    if not active_case:
        return redirect('case_create_view')

    if request.method == 'POST':
        pass

    ctx = {
        'active_case': active_case,
    }
    return render(request, 'import/misp.html', context=ctx)
