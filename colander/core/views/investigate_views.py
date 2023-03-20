import logging

import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt

from colander.core.forms import InvestigateSearchForm
from colander.core.models import colander_models, color_scheme, icons, BackendCredentials, ObservableType

THREAT_BACKEND_IDENTIFIER = 'threatr'
logger = logging.getLogger(__name__)
types = {t.short_name.lower(): t for t in ObservableType.objects.all()}


def get_threatr_types(api_key):
    headers = {'Authorization': f'Token {api_key}'}
    response = requests.get(f'{settings.THREATR_BASE_URL}/api/types', headers=headers)
    if response.status_code < 300:
        return response.json()
    return []

@login_required
@csrf_exempt
def investigate_search_view(request):
    form = InvestigateSearchForm()
    results = {}
    wait = False
    types_to_display = {}
    mermaid = ''

    if request.GET.keys():
        credentials = BackendCredentials.objects.filter(backend=THREAT_BACKEND_IDENTIFIER)
        if not credentials:
            messages.info(request, 'This relation already exists.', extra_tags='danger')
            logger.error(f'No credentials found for module {THREAT_BACKEND_IDENTIFIER}')

        credentials = credentials.first()
        api_key = credentials.credentials.get('api_key')
        threatr_types = get_threatr_types(api_key)
        if not threatr_types:
            logger.error(f'Unable to retrieve threatr types')

        entities = {}
        form = InvestigateSearchForm(request.GET)
        if form.is_valid():
            data = {
                "super_type": "observable",
                "type": form.cleaned_data.get('type'),
                "value": form.cleaned_data.get('value'),
                "force": form.cleaned_data.get('force_update')
            }
            headers = {'Authorization': f'Token {api_key}'}
            response = requests.post(f'{settings.THREATR_BASE_URL}/api/request/', headers=headers, json=data)
            print(response.status_code)
            print(response.json())
            wait = response.status_code == 201
            if response.status_code == 200:
                results = response.json()
                entity_super_type = results.get('root_entity').get('super_type').get('name')
                if entity_super_type in colander_models:
                    model = colander_models[entity_super_type]
                    if model in color_scheme:
                        results['root_entity']['color'] = color_scheme[model]
                for entity in results.get('entities'):
                    types_to_display[entity.get('super_type').get('short_name')] = entity.get('super_type')
                    entity_super_type = entity.get('super_type').get('name')
                    if entity_super_type in colander_models:
                        model = colander_models[entity_super_type]
                        if model in color_scheme:
                            entity['color'] = color_scheme[model]
                    entities[entity.get('id')] = entity
                results['entities'] = entities
                # types_to_display = list(types_to_display.values())
                # types_to_display.sort(key=lambda v: v.get('name'), reverse=False)

    return render(
        request,
        'pages/investigate/base.html',
        {
            'form': form,
            # 'results': [],
            'results': results,
            'mermaid': mermaid,
            'types_to_display': types_to_display,
            'types': types,
            # 'wait': True,
            'wait': wait,
        }
    )
