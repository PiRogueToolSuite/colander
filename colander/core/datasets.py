from colander.core.models import colander_models, color_scheme, icons, icons_unicodes


def __getattr__(name):
    if f'__{name}' in globals():
        return globals()[f'__{name}']()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def __all_styles():
    all_styles = {}

    for name, model in colander_models.items():
        if model not in icons:
            continue
        all_styles[name] = {
            'icon-font-classname': icons[model],
            'icon-font-unicode': icons_unicodes[model],
            'icon-svg': None,
            'color': color_scheme[model],
            'types': {}
        }
        if hasattr(model, 'type'):
            for model_type in model.type.get_queryset().all():
                mtid = model_type.short_name
                if mtid in all_styles[name]['types']:
                    print("WARNING", f"all_styles already contains {mtid} entry. Occurs for model:{model}.")
                all_styles[name]['types'][mtid] = {
                    'name': model_type.name,
                    'icon-font-classname': model_type.nf_icon,
                    'icon-font-unicode': None,
                    'icon-svg': model_type.svg_icon,
                    'color': None
                }

    return all_styles


def __creatable_entity_and_types():
    models = []
    types = {}
    common_fields = [
            {'label': 'Value or name', 'name': 'name', 'required': True, 'multiple': False},
            # {'label': 'TLP', 'name': 'tlp', 'required': False, 'multiple': False},
            # {'label': 'PAP', 'name': 'pap', 'required': False, 'multiple': False},
            {'label': 'Description', 'name': 'description', 'required': False, 'multiple': False},
            {'label': 'Source URL', 'name': 'source_url', 'required': False, 'multiple': False},
            {'label': 'Ignore', 'name': 'ignored_field', 'required': False, 'multiple': True},
    ]
    extra_fields =  [{'label': 'Extra attribute', 'name': 'attributes', 'required': False, 'multiple': True}]
    fields = {
        'ACTOR': common_fields,
        'DEVICE': common_fields + extra_fields,
        'OBSERVABLE': common_fields + extra_fields,
        'THREAT': common_fields,
        'DATAFRAGMENT': common_fields + [{'label': 'Content', 'name': 'content', 'required': True, 'multiple': False}],
    }
    exclude = ['Artifact', 'Case', 'DetectionRule', 'EntityRelation', 'Event']
    for name, model in colander_models.items():
        if hasattr(model, 'type') and name not in exclude:
            models.append({
                 'name': name,
                 'short_name': name.upper(),
                 'fields': fields.get(name.upper(), []),
            })
            types[name.upper()] = [
                {
                    'label': t.name,
                    'name': t.name,
                    'id': t.short_name,
                }
                for t in model.type.get_queryset().all()
            ]
            types[name] = types[name.upper()]

    model_data = {
        'models': models,
        'super_types': models,
        'types': types
    }

    return model_data
