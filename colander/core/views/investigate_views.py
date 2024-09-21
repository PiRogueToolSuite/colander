import logging

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from colander.core.forms import InvestigateSearchForm
from colander.core.models import ObservableType, colander_models, color_scheme
from colander.core.threatr import ThreatrClient

THREAT_BACKEND_IDENTIFIER = 'threatr'
logger = logging.getLogger(__name__)


def get_threatr_types(api_key):
    headers = {'Authorization': f'Token {api_key}'}
    response = requests.get(f'{settings.THREATR_BASE_URL}/api/types', headers=headers)
    if response.status_code < 300:
        return response.json()
    return []


@login_required
@csrf_exempt
def investigate_search_view(request):
    threatr_client = ThreatrClient()
    threatr_results = {}
    wait = False
    mermaid = ''
    types = {}
    ordering = {}
    request_data = {}

    correctly_configured, message = threatr_client.is_correctly_configured()
    if not correctly_configured:
        messages.error(request, message, extra_tags='danger')
        logger.error(f'Threatr is not correctly configured. {THREAT_BACKEND_IDENTIFIER}. {message}')
        return render(
            request,
            'pages/investigate/base.html',
            {
                'form': None,
                'request_data': request_data,
                'results': threatr_results,
                'mermaid': mermaid,
                'types': types,
                'wait': wait,
            }
        )

    types = threatr_client.get_supported_types()
    form = InvestigateSearchForm()

    if request.GET.keys():
        entities = {}
        form = InvestigateSearchForm(request.GET)
        if form.is_valid():
            request_data = {
                "super_type": form.cleaned_data.get('super_type'),
                "type": form.cleaned_data.get('type'),
                "value": form.cleaned_data.get('value'),
                "force": form.cleaned_data.get('force_update', False)
            }
            threatr_results, wait = threatr_client.send_request(request_data)
            request_data.pop('force', False)
            if not wait and type(threatr_results) is dict:
                ordering = {'global':{
                    'total': len(threatr_results['entities']),
                    'events': len(threatr_results['events']),
                    'entities': 0,
                    'external_doc': 0,
                    },
                    # ToDo: get rid of the hardcoded list of types
                    'importable_types': ['OBSERVABLE', 'DEVICE', 'THREAT'],
                    'types': {
                    }
                }
                external_doc_entities = []
                root_entity = threatr_results.get('root_entity')
                root_entity_super_type_name = root_entity.get('super_type').get('name')
                root_entity_super_type_short_name = root_entity.get('super_type').get('short_name')
                # List the root entity as a result
                ordering['types'][root_entity_super_type_short_name] = {
                    'super_type': root_entity.get('super_type'),
                    'entities': [root_entity],
                    'count': 1
                }
                # Map the root entity types from Threatr with Colander models and types
                if root_entity_super_type_name in colander_models:
                    model = colander_models[root_entity_super_type_name]
                    # Apply Colander colors
                    if model in color_scheme:
                        threatr_results['root_entity']['color'] = color_scheme[model]
                for entity in threatr_results.get('entities'):
                    entity_super_type = entity.get('super_type')
                    entity_super_type_short_name = entity_super_type.get('short_name')
                    entity_super_type_name = entity_super_type.get('name')
                    # Put the external documentations such as reports into a separate list
                    if entity_super_type_short_name == 'EXT_DOC':
                        ordering['global']['external_doc'] += 1
                        external_doc_entities.append(entity)
                        continue
                    else:
                        ordering['global']['entities'] += 1
                    # Count the number of results per super type
                    if entity_super_type_short_name not in ordering['types']:
                        ordering['types'][entity_super_type_short_name] = {
                            'super_type': entity_super_type,
                            'entities': [],
                            'count': 0 }
                    ordering['types'][entity_super_type_short_name]['count'] += 1
                    ordering['types'][entity_super_type_short_name]['entities'].append(entity)
                    # Apply Colander colors
                    if entity_super_type_name in colander_models:
                        model = colander_models[entity_super_type_name]
                        if model in color_scheme:
                            entity['color'] = color_scheme[model]
                    entities[entity.get('id')] = entity

                # Sort the entities
                for super_type, obj in ordering['types'].items():
                    obj['entities'] = sorted(obj['entities'], key=lambda x: x.get('type').get('name'))
                threatr_results['entities'] = entities
                threatr_results['reports'] = external_doc_entities

    return render(
        request,
        'pages/investigate/base.html',
        {
            'form': form,
            'threatr_url': settings.THREATR_BASE_URL,
            'request_data': request_data,  # parameters of the request
            'results': threatr_results,  # the results returned by Threatr
            'ordering': ordering,  # in which order the results should be shown
            'mermaid': mermaid,  # the mermaid graph
            'models': types,  # the different types of entities to list
            'wait': wait,  # True if we are waiting for the completion of the request sent to Threatr
        }
    )
