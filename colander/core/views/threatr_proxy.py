import logging

from django.contrib.auth.decorators import login_required

from colander.core.models import BackendCredentials

THREAT_BACKEND_IDENTIFIER='threatr'
logger = logging.getLogger(__name__)

@login_required
def request_threatr_view(request):
    credentials = BackendCredentials.objects.filter(backend=THREAT_BACKEND_IDENTIFIER)
    if not credentials:
        logger.error(f'No credentials found for module {THREAT_BACKEND_IDENTIFIER}')
        return None
