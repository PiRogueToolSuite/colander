
import re
import requests
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.http import QueryDict
from django.views.decorators.csrf import csrf_exempt

from urllib.parse import urlparse


@csrf_exempt
@login_required
def cyber_chef_view(request, path=''):
    print(path)
    path = path.replace('cyberchef/', '')
    if path.startswith('input'):
        path = f'#{path}'
    remote_url = 'http://cyberchef:8000/' + path
    overrides = [
        ('assets/', 'cyberchef/assets/'),
        ('modules/', 'cyberchef/modules/'),
        ('images/', 'cyberchef/images/'),
    ]
    return generic_proxy_view(request, remote_url, {}, overrides=overrides)


def generic_proxy_view(request, url, requests_args=None, overrides=None):
    """
    Forward as close to an exact copy of the request as possible along to the
    given url.  Respond with as close to an exact copy of the resulting
    response as possible.
    If there are any additional arguments you wish to send to requests, put
    them in the requests_args dictionary.
    """
    requests_args = (requests_args or {}).copy()
    headers = get_headers(request.META)
    params = request.GET.copy()

    if 'headers' not in requests_args:
        requests_args['headers'] = {}
    if 'data' not in requests_args:
        requests_args['data'] = request.body
    if 'params' not in requests_args:
        requests_args['params'] = QueryDict('', mutable=True)

    # Overwrite any headers and params from the incoming request with explicitly
    # specified values for the requests library.
    headers.update(requests_args['headers'])
    params.update(requests_args['params'])

    # If there's a content-length header from Django, it's probably in all-caps
    # and requests might not notice it, so just remove it.
    for key in list(headers.keys()):
        if key.lower() == 'content-length':
            del headers[key]

    requests_args['headers'] = headers
    requests_args['params'] = params

    response = requests.request(request.method, url, **requests_args)
    content = response.content
    if overrides:
        try:
            decoded_content = content.decode('utf-8')
            for a, b in overrides:
                decoded_content = decoded_content.replace(a, b)
            content = decoded_content.encode('utf-8')
        except:
            pass

    proxy_response = HttpResponse(
        content,
        status=response.status_code)

    excluded_headers = {'connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization', 'te', 'trailers',
                        'transfer-encoding', 'upgrade', 'content-encoding', 'content-length'}
    for key, value in response.headers.items():
        if key.lower() in excluded_headers:
            continue
        elif key.lower() == 'location':
            # If the location is relative at all, we want it to be absolute to
            # the upstream server.
            proxy_response[key] = make_absolute_location(response.url, value)
        else:
            proxy_response[key] = value

    return proxy_response


def make_absolute_location(base_url, location):
    """
    Convert a location header into an absolute URL.
    """
    absolute_pattern = re.compile(r'^[a-zA-Z]+://.*$')
    if absolute_pattern.match(location):
        return location

    parsed_url = urlparse(base_url)

    if location.startswith('//'):
        # scheme relative
        return parsed_url.scheme + ':' + location

    elif location.startswith('/'):
        # host relative
        return parsed_url.scheme + '://' + parsed_url.netloc + location

    else:
        # path relative
        return parsed_url.scheme + '://' + parsed_url.netloc + parsed_url.path.rsplit('/', 1)[0] + '/' + location

    return location


def get_headers(environ):
    """
    Retrieve the HTTP headers from a WSGI environment dictionary.  See
    https://docs.djangoproject.com/en/dev/ref/request-response/#django.http.HttpRequest.META
    """
    headers = {}
    for key, value in environ.items():
        # Sometimes, things don't like when you send the requesting host through.
        if key.startswith('HTTP_') and key != 'HTTP_HOST':
            headers[key[5:].replace('_', '-')] = value
        elif key in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
            headers[key.replace('_', '-')] = value

    return headers
