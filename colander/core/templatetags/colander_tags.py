from base64 import urlsafe_b64encode

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
        return instance[name]
    except:
        try:
            return getattr(instance, name)
        except:
            return ''


@register.filter(name="b64")
def to_b64(instance):
    if type(instance) is not str:
        return instance
    encoded = instance.encode('utf-8')
    return urlsafe_b64encode(encoded).decode()


@register.filter(name="to_cyberchef_input")
def to_cyberchef_input(instance):
    if type(instance) is not str:
        return instance
    encoded = instance.encode('utf-8')
    return f'input={urlsafe_b64encode(encoded).decode()}'
