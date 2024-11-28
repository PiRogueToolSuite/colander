from django.conf import settings
from django.shortcuts import render

from colander.core.threatr import ThreatrClient


def colander_status_view(request):
    client = ThreatrClient()
    colander_git_commit_hash = ''
    try:
        colander_git_commit_hash = settings.GIT_COMMIT_HASH
    except: pass
    return render(
        request,
        'pages/status/base.html',
        context={
            'threatr': client.get_status(),
            'colander': {
                'git_commit_hash': colander_git_commit_hash
            }
        }
    )
