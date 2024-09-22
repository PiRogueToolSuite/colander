import datetime
import json
from base64 import urlsafe_b64encode
from datetime import timedelta

from django import template
from django.utils.dateparse import parse_datetime
from django.utils.timesince import timeuntil
from rest_framework.fields import DateTimeField

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

@register.filter(name="humanize_duration")
def to_humanized_duration(instance):
    return "{:0>8}".format(str(timedelta(seconds=int(instance))))

@register.filter(name="to_datetime")
def to_datetime(instance):
    if not instance or type(instance) is not str:
        return instance
    return parse_datetime(str(instance))

@register.filter(name="humanize_event_duration")
def to_humanized_event_duration(instance):
    start = parse_datetime(instance.get('first_seen'))
    end = parse_datetime(instance.get('last_seen'))
    return timeuntil(end, start)

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


@register.filter(name="json_format")
def json_format(obj, indent=2):
    if not obj or type(obj) is not dict:
        return obj
    formatted = obj.copy()
    try:
        formatted = json.dumps(formatted, indent=indent)
    except:
        pass
    return formatted


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
