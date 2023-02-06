from django import template
register = template.Library()

@register.filter(name="model_name")
def model_name(instance):
    return instance._meta.verbose_name

@register.filter(name="escape_space")
def escape_space(instance):
    if type(instance) is str:
        return instance.replace(' ', '\ ')
    return ''

@register.filter(name="get_field")
def get_field(instance, name):
    try:
        return instance.get(name, '')
    except:
        try:
            return getattr(instance, name)
        except:
            return ''
