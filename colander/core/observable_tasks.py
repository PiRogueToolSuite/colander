from tempfile import NamedTemporaryFile
from zipfile import ZipFile

import requests

from colander.core.artifact_utils import import_file_as_artifact
from colander.core.models import ArtifactType, EntityRelation, Observable


def capture_url(observable_id):
    url_object = Observable.objects.get(id=observable_id)
    payload = {
        'url': url_object.name
    }
    response = requests.post('http://playwright:80/capture', json=payload)
    if response.status_code == 200:
        with NamedTemporaryFile() as out:
            out.write(response.content)
            with ZipFile(out.name, 'r') as archive:
                with archive.open('screenshot.png') as screenshot_file:
                    screenshot = import_file_as_artifact(
                        screenshot_file,
                        url_object.owner,
                        url_object.case,
                        ArtifactType.objects.get(short_name='IMAGE'),
                        'webpage_screenshot.png',
                        'image/png',
                        url_object.tlp,
                        url_object.pap,
                    )
                    relation = EntityRelation(
                        name='screenshot of',
                        owner=url_object.owner,
                        case=url_object.case,
                        obj_from=screenshot,
                        obj_to=url_object
                    )
                    relation.save()
                with archive.open('capture.har') as screenshot_file:
                    har = import_file_as_artifact(
                        screenshot_file,
                        url_object.owner,
                        url_object.case,
                        ArtifactType.objects.get(short_name='HAR'),
                        'webpage_traffic.har',
                        'application/json',
                        url_object.tlp,
                        url_object.pap,
                    )
                    relation = EntityRelation(
                        name='HTTP traffic of',
                        owner=url_object.owner,
                        case=url_object.case,
                        obj_from=har,
                        obj_to=url_object
                    )
                    relation.save()
