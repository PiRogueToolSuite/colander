import datetime
import json
import logging

import requests
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render
from elasticsearch_dsl import Date, Document, Index, Keyword, Object

from colander.core.models import Observable
from colander.core.scarlet_utils import clean_results

SCARLETSHARK_API_BASE_URL = 'https://api.scarletshark.com'
SCARLETSHARK_AUTH_HEADER = {'Authorization': 'Bearer a4460b-6b02fe-71099a-adc9f5-08adf9'}
logger = logging.getLogger(__name__)


class ObservableEnrichment(Document, LoginRequiredMixin):
    owner = Keyword(required=True)
    type = Keyword()
    case_id = Keyword()
    observable_id = Keyword()
    enrichment_date = Date()
    data = Object()


@login_required
def enrich_observable(request, observable_id):
    from elasticsearch_dsl import connections
    connections.create_connection(hosts=['elasticsearch'], timeout=20)
    result = None
    in_error = True
    cached = False
    observable = get_object_or_404(Observable, id=observable_id)

    # set up elastic search index
    index_name = f'{observable.get_es_index()}.e'
    try:
        index = Index(index_name)
        if not index.exists():
            index.create()
            ObservableEnrichment.init(index=index_name)
    except Exception as e:
        logger.error(e)

    # Check if an enrichment already exists
    enrichment = None
    try:
        enrichment = ObservableEnrichment.get(str(observable.id), index=index_name)
        cached = True
    except Exception as e:
        logger.error(e)

    if enrichment:
        result = enrichment.data
    # if True:
    else:
        enrichment = ObservableEnrichment()
        enrichment.meta.id = str(observable_id)
        enrichment.owner = str(request.user.id)
        enrichment.case_id = str(observable.case.id)
        enrichment.observable_id = str(observable_id)
        enrichment.enrichment_date = datetime.datetime.now().isoformat()

        if observable.type.short_name.lower() == 'ipv4' or observable.type.short_name.lower() == 'ipv6':
            url = f'{SCARLETSHARK_API_BASE_URL}/v0.3/search_ip.php?ips[]={observable.value}'
            response = requests.get(url, headers=SCARLETSHARK_AUTH_HEADER)
            if response.status_code == 200:
                result = response.json()
                in_error, result = clean_results(result)
        elif observable.type.short_name.lower() == 'domain':
            url = f'{SCARLETSHARK_API_BASE_URL}/v0.2/search_domain.php?domain={observable.value}'
            response = requests.get(url, headers=SCARLETSHARK_AUTH_HEADER)
            if response.status_code == 200:
                result = response.json()
                in_error, result = clean_results(result)
        else:
            pass

        if result:
            enrichment.data = result
            enrichment.save(index=index_name)

    if type(result) is dict:
        raw_data = json.dumps(result, indent=2)
    else:
        raw_data = json.dumps(result.to_dict(), indent=2)

    return render(
        request,
        'pages/analyze/base.html',
        {
            'observable': observable,
            'enrichment': enrichment,
            'in_error': in_error,
            'raw': raw_data,
            'source': 'Scarlet Shark',
            'cached': cached
        }
    )
