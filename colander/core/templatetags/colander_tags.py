from base64 import urlsafe_b64encode

from django import template
register = template.Library()

@register.filter(name="model_name")
def model_name(instance):
    if type(instance) is dict:
        return ''
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
    return urlsafe_b64encode(encoded).decode().replace('=', '')


@register.filter(name="to_cyberchef_input")
def to_cyberchef_input(instance):
    if type(instance) is not str:
        return instance
    encoded = instance.encode('utf-8')
    return f'input={urlsafe_b64encode(encoded).decode()}'


@register.filter(name="to_title")
def to_title(instance):
    if not instance or type(instance) is not str:
        return instance
    words = instance.split('_')
    words[0] = words[0].title()
    title = ' '.join(words)
    return title


@register.filter(name="split")
def split(instance, delim):
    if not instance or type(instance) is not str:
        return instance
    words = instance.split(delim)
    return words


@register.simple_tag(takes_context=True)
def active_link(context, view_url, *args, **kwargs):
    """
    Returns 'active' class name if the given view url in the current context path.

    :param context: the view rendering context
    :param view_url: the view url tested
    :return: 'active' string or empty string ('')
    """
    request = context.get('request')
    if request is None:
        # Can't work without the request object.
        return ''

    if request.path.startswith(view_url):
        return 'active'
    else:
        return ''


@register.simple_tag
def define(val=None):
    return val


@register.filter(name="bs_alert_level_class")
def bs_alert_level_class(message_tag_level):
    if message_tag_level == 'error':
        return 'danger'
    return message_tag_level
