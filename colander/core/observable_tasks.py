import asyncio
import io
import ipaddress
import json
import logging
import socket
from urllib.parse import urlparse

from django.conf import settings
from django.db import transaction
from lookyloo_models import CaptureSettings
from playwrightcapture import Capture

from colander.core.artifact_utils import import_file_as_artifact
from colander.core.models import ArtifactType, EntityRelation, Observable
from colander.core.signals import artifact_ready_for_analysis
from colander.websocket.consumers import CaseContextConsumer

logger = logging.getLogger(__name__)


def capture_url(observable_id):
    if not settings.USE_PLAYWRIGHT:
        logger.warning('Playwright is disabled')
        return

    observable_url = Observable.objects.get(id=observable_id)
    url_str = observable_url.value

    try:
        parsed_url = urlparse(url_str)
        host = parsed_url.hostname
        logger.debug("Host from url: %s", host)
    except Exception as e:
        logger.error("Can't capture url: No host part in the given url: %s, traceback = ",
                     url_str,
                     exc_info=e)
        return

    try:
        ips_addr = [ipaddress.ip_address(host)]
    except ValueError:
        logger.debug("Host not an ip address: %s", host)

        addr_info = socket.getaddrinfo(host, None)
        ips_addr = {ipaddress.ip_address(info[4][0]) for info in addr_info}

    for ip in ips_addr:
        logger.debug(f"Associated ip addr: %s", ip)
        logger.debug(f"        ip_private: %s", ip.is_private)
        logger.debug(f"       is_loopback: %s", ip.is_loopback)
        logger.debug(f"     is_link_local: %s", ip.is_link_local)
        logger.debug(f"       is_reserved: %s", ip.is_reserved)
        logger.debug(f"         is_global: %s", ip.is_global)
        if not ip.is_global:
            logger.error("Can't capture url: ip not global: %s", ip)
            return
    try:
        entries = asyncio.run(_synced_capture_url(url_str))
    except Exception as e:
        logger.error(f"Page capture failed: %s", e)
        return

    screenshot_file = io.BytesIO(entries.get('png'))
    #html_file = io.StringIO(entries.get('html').encode('utf-8'))
    har_file = io.BytesIO(json.dumps(entries.get("har")).encode('utf-8'))

    screenshot = import_file_as_artifact(
        screenshot_file,
        observable_url.owner,
        observable_url.case,
        ArtifactType.objects.get(short_name='IMAGE'),
        'webpage_screenshot.png',
        'image/png',
        observable_url.tlp,
        observable_url.pap,
    )
    relation = EntityRelation(
        name='screenshot of',
        owner=observable_url.owner,
        case=observable_url.case,
        obj_from=screenshot,
        obj_to=observable_url
    )
    relation.save()

    har = import_file_as_artifact(
        har_file,
        observable_url.owner,
        observable_url.case,
        ArtifactType.objects.get(short_name='HAR'),
        'webpage_traffic.har',
        'application/json',
        observable_url.tlp,
        observable_url.pap,
    )
    relation = EntityRelation(
        name='HTTP traffic of',
        owner=observable_url.owner,
        case=observable_url.case,
        obj_from=har,
        obj_to=observable_url
    )
    relation.save()

    transaction.on_commit(
        lambda:
            artifact_ready_for_analysis.send(sender=capture_url.__class__, artifact_id=str(screenshot.id))
    )
    transaction.on_commit(
        lambda:
            artifact_ready_for_analysis.send(sender=capture_url.__class__, artifact_id=str(har.id))
    )

    # Send notifications ...
    CaseContextConsumer.send_message_to_user_consumers(observable_url.owner, {
        'msg': 'A new capture has been done',
        'detail': 'Screenshot and HAR',
        'url': observable_url.get_absolute_url(),
    })


async def _synced_capture_url(url:str):

    capture_settings = CaptureSettings(url=url)
    async with Capture(capture_settings=capture_settings, only_global_lookup=True) as capture:
        await capture.initialize_context()
        entries = await capture.capture_page(max_depth_capture_time=10)

    return entries
