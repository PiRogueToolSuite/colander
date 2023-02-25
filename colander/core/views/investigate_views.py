import requests
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from colander.core.forms import InvestigateSearchForm
from colander.core.models import ObservableType, colander_models, color_scheme, icons

data = {
    "input": {
        "reference": "990cbd78-f73f-4528-9f58-361ecbd110cd",
        "obj_type": "observable",
        "type": "domain",
        "value": "0x39b.fr"
    },
    "module": "dns_records"
}

results = {'input': {'reference': '990cbd78-f73f-4528-9f58-361ecbd110cd', 'obj_type': 'observable', 'type': 'domain',
                     'value': '0x39b.fr', 'request_id': '2db95959-b34f-4a75-ba32-d61ac59c0b21',
                     'requested_at': '2023-02-06T14:55:06.748656'}, 'results': [
    {'id': 'b771d1c6-622e-4499-a513-0086c5d742dc', 'correlation_id': 'ba020295-4f7d-4f35-904a-b23b912c8247',
     'attributes': [], 'description': '', 'type': 'dns_record', 'value': 'A 37.59.50.218', 'obj_type': 'observable'},
    {'id': '55ff51b9-5364-4c35-9754-1e7af18ac3d1', 'correlation_id': 'ba020295-4f7d-4f35-904a-b23b912c8247',
     'attributes': [], 'description': '', 'name': 'related to', 'obj_from': 'b771d1c6-622e-4499-a513-0086c5d742dc',
     'obj_to': '990cbd78-f73f-4528-9f58-361ecbd110cd', 'obj_type': 'relation'},
    {'id': 'b7b86df5-37fb-4a66-ad3e-1aa20461b267', 'correlation_id': 'ba020295-4f7d-4f35-904a-b23b912c8247',
     'attributes': [], 'description': '', 'type': 'ipv4', 'value': '37.59.50.218', 'obj_type': 'observable'},
    {'id': 'a76ee80e-663b-44bc-be88-e886ddf5291e', 'correlation_id': 'ba020295-4f7d-4f35-904a-b23b912c8247',
     'attributes': [], 'description': '', 'name': 'resolves', 'obj_from': 'b7b86df5-37fb-4a66-ad3e-1aa20461b267',
     'obj_to': '990cbd78-f73f-4528-9f58-361ecbd110cd', 'obj_type': 'relation'},
    {'id': 'cf040753-a0bc-479f-8069-8c626d6ab5ec', 'correlation_id': 'ba020295-4f7d-4f35-904a-b23b912c8247',
     'attributes': [], 'description': '', 'type': 'dns_record', 'value': 'NS ns1093.ui-dns.de.',
     'obj_type': 'observable'},
    {'id': '640c66fc-a27a-412c-8265-64898250586c', 'correlation_id': 'ba020295-4f7d-4f35-904a-b23b912c8247',
     'attributes': [], 'description': '', 'name': 'related to', 'obj_from': 'cf040753-a0bc-479f-8069-8c626d6ab5ec',
     'obj_to': '990cbd78-f73f-4528-9f58-361ecbd110cd', 'obj_type': 'relation'},
    {'id': 'bb9207f2-45a4-4a81-b8c9-5118a0f6d196', 'correlation_id': 'ba020295-4f7d-4f35-904a-b23b912c8247',
     'attributes': [], 'description': '', 'type': 'dns_record', 'value': 'NS ns1093.ui-dns.biz.',
     'obj_type': 'observable'},
    {'id': 'dd3bcf1f-05f0-4dcc-a2a3-9e2a228922ec', 'correlation_id': 'ba020295-4f7d-4f35-904a-b23b912c8247',
     'attributes': [], 'description': '', 'name': 'related to', 'obj_from': 'bb9207f2-45a4-4a81-b8c9-5118a0f6d196',
     'obj_to': '990cbd78-f73f-4528-9f58-361ecbd110cd', 'obj_type': 'relation'},
    {'id': '68af371b-6258-4f19-bfb7-9291fdcc43dd', 'correlation_id': 'ba020295-4f7d-4f35-904a-b23b912c8247',
     'attributes': [], 'description': '', 'type': 'dns_record', 'value': 'NS ns1093.ui-dns.com.',
     'obj_type': 'observable'},
    {'id': '5d06d0bb-e083-4595-a3fd-f1766e8fb1b8', 'correlation_id': 'ba020295-4f7d-4f35-904a-b23b912c8247',
     'attributes': [], 'description': '', 'name': 'related to', 'obj_from': '68af371b-6258-4f19-bfb7-9291fdcc43dd',
     'obj_to': '990cbd78-f73f-4528-9f58-361ecbd110cd', 'obj_type': 'relation'},
    {'id': 'cde98128-67f4-4cda-a27c-79ced4d8498e', 'correlation_id': 'ba020295-4f7d-4f35-904a-b23b912c8247',
     'attributes': [], 'description': '', 'type': 'dns_record', 'value': 'NS ns1093.ui-dns.org.',
     'obj_type': 'observable'},
    {'id': '1bcacf2e-bcb3-4f38-9737-03b79d65304e', 'correlation_id': 'ba020295-4f7d-4f35-904a-b23b912c8247',
     'attributes': [], 'description': '', 'name': 'related to', 'obj_from': 'cde98128-67f4-4cda-a27c-79ced4d8498e',
     'obj_to': '990cbd78-f73f-4528-9f58-361ecbd110cd', 'obj_type': 'relation'},
    {'id': 'ecb3defc-2bdd-44f3-8334-1f0c2ed863f7', 'correlation_id': 'ba020295-4f7d-4f35-904a-b23b912c8247',
     'attributes': [], 'description': '', 'type': 'dns_record',
     'value': 'SOA ns1093.ui-dns.biz. hostmaster.1and1.com. 2016110439 28800 7200 604800 300',
     'obj_type': 'observable'},
    {'id': 'd31a77d6-fcad-41db-b6cb-bb5366e52857', 'correlation_id': 'ba020295-4f7d-4f35-904a-b23b912c8247',
     'attributes': [], 'description': '', 'name': 'related to', 'obj_from': 'ecb3defc-2bdd-44f3-8334-1f0c2ed863f7',
     'obj_to': '990cbd78-f73f-4528-9f58-361ecbd110cd', 'obj_type': 'relation'},
    {'id': '0733dec8-1b4f-443f-b0f5-515ea5b4177f', 'correlation_id': 'ba020295-4f7d-4f35-904a-b23b912c8247',
     'attributes': [], 'description': '', 'type': 'dns_record', 'value': 'MX 10 mx00.1and1.fr.',
     'obj_type': 'observable'},
    {'id': '1e9b0739-7591-4c34-ba13-4aa6d57f9a41', 'correlation_id': 'ba020295-4f7d-4f35-904a-b23b912c8247',
     'attributes': [], 'description': '', 'name': 'related to', 'obj_from': '0733dec8-1b4f-443f-b0f5-515ea5b4177f',
     'obj_to': '990cbd78-f73f-4528-9f58-361ecbd110cd', 'obj_type': 'relation'},
    {'id': 'e8d2f316-623a-46db-a9c3-a0d25b7c9cd8', 'correlation_id': 'ba020295-4f7d-4f35-904a-b23b912c8247',
     'attributes': [], 'description': '', 'type': 'dns_record', 'value': 'MX 11 mx01.1and1.fr.',
     'obj_type': 'observable'},
    {'id': '9ac8c3cb-cf89-434f-80e9-ac494fc9c3b0', 'correlation_id': 'ba020295-4f7d-4f35-904a-b23b912c8247',
     'attributes': [], 'description': '', 'name': 'related to', 'obj_from': 'e8d2f316-623a-46db-a9c3-a0d25b7c9cd8',
     'obj_to': '990cbd78-f73f-4528-9f58-361ecbd110cd', 'obj_type': 'relation'}]}

types = {t.short_name.lower(): t for t in ObservableType.objects.all()}


@login_required
def investigate_search_view(request):
    form = InvestigateSearchForm()
    results = {}
    mermaid = ''
    k = None
    if request.method == 'POST':
        form = InvestigateSearchForm(request.POST)
        if form.is_valid():
            data = {
                "input": {
                    "reference": "990cbd78-f73f-4528-9f58-361ecbd110cd",
                    "obj_type": "observable",
                    "type": form.cleaned_data.get('type'),
                    "value": form.cleaned_data.get('value')
                },
                "module": "dns_records"
            }
            response = requests.post('http://analyzers:6666/query', json=data)
            if response.status_code == 200:
                results = response.json()
                k = {}
                for r in results.get('results'):
                    k[r.get('id')] = r
                input = results.get('input')
                k[input.get('reference', '0')] = {
                    'id': input.get('reference'),
                    'obj_type': input.get('obj_type'),
                    'type': input.get('type'),
                    'value': input.get('value'),
                }
                nodes = []
                links = []
                classes = []
                for name, model in colander_models.items():
                    if model in color_scheme:
                        classes.append(f'classDef {name} fill:{color_scheme.get(model)}')
                for _, v in k.items():
                    if v.get('obj_type') != 'relation':
                        id = v.get('id')
                        value = v.get('value')
                        type = types.get(v.get('type'), '')
                        if type:
                            type = type.name
                        obj_type = v.get('obj_type')
                        print(obj_type)
                        icon = icons.get(colander_models.get(obj_type.title(), None), '')
                        icon_txt = ''
                        if icon:
                            icon_txt = f'fa:{icon}'
                        label = f'{id}("{icon_txt} {value}<br><small><i>{type}</i></small>")'
                        clazz = f'class {id} {obj_type.title()}'
                        nodes.append(label)
                        classes.append(clazz)
                    if v.get('obj_type') == 'relation':
                        obj_from = v.get('obj_from')
                        obj_to = v.get('obj_to')
                        label = f'{obj_from}-->{obj_to}'
                        links.append(label)

                node_txt = '\n\t'.join(list(set(nodes)))
                link_txt = '\n\t'.join(list(set(links)))
                class_txt = '\n\t'.join(list(set(classes)))
                mermaid = f'flowchart LR\n\t{node_txt}\n\t{link_txt}\n\t{class_txt}'

    return render(
        request,
        'pages/investigate/base.html',
        {
            'form': form,
            'input': results.get('input', None),
            'results': k,
            'mermaid': mermaid,
            'types': types
        }
    )
