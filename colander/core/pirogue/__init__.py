import logging
from typing import Dict

import environ
import grpc
from datetime import timedelta
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils import timezone
from django_q.models import Schedule
from grpc import RpcError
from pirogue_admin_client import PirogueAdminClientAdapter
from rest_framework.reverse import reverse

from colander.core.models import PiRogueCredentials, PiRogueStatus, DeviceMonitoring


def unschedule_pirogue_status_retrieval(pirogue_credentials_id):
    func=f'{_proceed_pirogue_status_retrieval.__module__}.{_proceed_pirogue_status_retrieval.__qualname__}'
    if not Schedule.objects.filter(func=func, args=f"'{pirogue_credentials_id}'").exists(): return
    Schedule.objects.get(func=func, args=f"'{pirogue_credentials_id}'").delete()


@receiver(pre_delete, sender=PiRogueCredentials, dispatch_uid='delete_pirogue_credentials_scheduled_task')
def delete_pirogue_credentials_scheduled_task(sender, instance: PiRogueCredentials, using, **kwargs):
    unschedule_pirogue_status_retrieval(str(instance.id))


def register_pirogue_status_retrieval_schedule(pirogue_credentials):
    func=f'{_proceed_pirogue_status_retrieval.__module__}.{_proceed_pirogue_status_retrieval.__qualname__}'
    #if Schedule.objects.filter(func=func, args=f"'{pirogue_credentials.id}'").exists(): return
    task, created = Schedule.objects.get_or_create(func=func, args=f"'{pirogue_credentials.id}'",
                                          defaults={'schedule_type': 'H'})
    if pirogue_credentials.friendly_name:
        task.name = f"{pirogue_credentials.friendly_name} heartbeat"
    else:
        task.name = f"{pirogue_credentials.host}:{pirogue_credentials.port} heartbeat"

    task.save()

    register_pirogue_status_cleaner()


def _safe_update_pirogue_operating_mode(pirogue_credentials, pirogue_admin_client_adapter, grpc_status):

    try:
        operating_mode = None

        if grpc_status:
            # We may found 'operating mode' in status response payload
            if 'sections' in grpc_status:
                for section in grpc_status['sections']:
                    if section['name'] != 'system': continue
                    for item in section['items']:
                        if item['name'] != 'operating-mode': continue
                        operating_mode = item['state']
        else:
            # We may rely on get_configuration to retrieve 'operating mode'
            configuration = pirogue_admin_client_adapter.get_configuration()
            operating_mode = configuration.get('SYSTEM_OPERATING_MODE', None)
            if operating_mode is None:
                logging.warning('safe_update_pirogue_operating_mode fail', 'SYSTEM_OPERATING_MODE entry not found')

        pirogue_credentials.operating_mode = operating_mode
        pirogue_credentials.save()
    except Exception as exception:
        logging.warning('safe_update_pirogue_operating_mode fail', exception)


def _proceed_pirogue_status_retrieval(pirogue_credentials_id):

    prc = None
    try:
        prc = PiRogueCredentials.objects.get(pk=pirogue_credentials_id)
    except PiRogueCredentials.DoesNotExist:
        unschedule_pirogue_status_retrieval(pirogue_credentials_id)
        return

    ps = PiRogueStatus.objects.create(pirogue_credentials=prc)
    certificate = 'public' if prc.has_public_visibility else prc.certificate
    paca = PirogueAdminClientAdapter(prc.host, prc.port, prc.token, certificate)

    try:
        status = paca.get_status()
        _safe_update_pirogue_operating_mode(prc, paca, status)
    except RpcError as rpc_error:
        if rpc_error.code() == grpc.StatusCode.UNIMPLEMENTED:
            # Special case where first version of PiRogueAdmin server
            # does not support 'status' query
            # BUT
            # this means its PiRogueCredentials configuration is correct and is working.
            ps.success = True
        else:
            ps.success = False
        ps.error = rpc_error.details()
        ps.save()
        _safe_update_pirogue_operating_mode(prc, paca, None)
    except Exception as exception:
        ps.success = False
        ps.error = str(exception)
        ps.save()
    else:
        ps.success = True
        ps.content = status
        ps.save()


def register_pirogue_status_cleaner():
    func=f'{_proceed_pirogue_status_cleaner.__module__}.{_proceed_pirogue_status_cleaner.__qualname__}'
    if Schedule.objects.filter(func=func).exists(): return
    task, created = Schedule.objects.get_or_create(func=func,
                                                   defaults={'schedule_type': Schedule.DAILY},
                                                   name='PiRogue Status Cleaner')


def _proceed_pirogue_status_cleaner():
    all_pirogue_credentials = (PiRogueStatus.objects
                               .order_by('pirogue_credentials')
                               .values_list('pirogue_credentials', flat=True)
                               .distinct())
    for pirogue_credentials in all_pirogue_credentials:
        all_older_status = (PiRogueStatus.objects
                            .filter(pirogue_credentials=pirogue_credentials,
                                    reported_at__lt=(timezone.now() - timedelta(days=3)))
                            .values_list("id", flat=True))
        PiRogueStatus.objects.filter(pk__in=list(all_older_status)).delete()


def register_device_monitoring_auto_stopper():
    func=f'{_proceed_device_monitoring_auto_stopper.__module__}.{_proceed_device_monitoring_auto_stopper.__qualname__}'
    if Schedule.objects.filter(func=func).exists(): return
    task, created = Schedule.objects.get_or_create(func=func,
                                                   defaults={'schedule_type': Schedule.HOURLY},
                                                   name='Device Monitoring Auto-Stopper')


def unschedule_device_monitoring_auto_stopper():
    func=f'{_proceed_device_monitoring_auto_stopper.__module__}.{_proceed_device_monitoring_auto_stopper.__qualname__}'
    schedule = Schedule.objects.filter(func=func)
    if schedule.exists():
        schedule.delete()


def _proceed_device_monitoring_auto_stopper():
    all_running_device_monitorings = DeviceMonitoring.objects.filter(status=1).all()

    if len(all_running_device_monitorings) > 0:
        for running_device_monitoring in all_running_device_monitorings:
            supposed_ended_at = running_device_monitoring.started_at + timedelta(days=running_device_monitoring.duration)
            if timezone.now() > supposed_ended_at:
                result = delete_device_monitoring(running_device_monitoring)
                if result['success']:
                    running_device_monitoring.status = 2 # 'Finished'
                    running_device_monitoring.ended_at = timezone.now()
                    running_device_monitoring.save()
    else:
        unschedule_device_monitoring_auto_stopper()


def get_configuration(pirogue_credentials_id):
    prc = PiRogueCredentials.objects.get(pk=pirogue_credentials_id)

    response = dict({ "success": False, "error": None })

    try:
        certificate = 'public' if prc.has_public_visibility else prc.certificate
        paca = PirogueAdminClientAdapter(prc.host, prc.port, prc.token, certificate)
        content = paca.get_configuration()
    except RpcError as rpc_error:
        response['success'] = False
        response['grpc_success'] = True
        response['error'] = rpc_error.details()
    except Exception as exception:
        response['success'] = False
        response['grpc_success'] = False
        response['error'] = str(exception)
    else:
        response['success'] = True
        response['grpc_success'] = True
        response['content'] = content

    return response


def get_packages_info(pirogue_credentials_id):
    prc = PiRogueCredentials.objects.get(pk=pirogue_credentials_id)

    response = dict({ "success": False, "grpc_success": False, "error": None })

    try:
        certificate = 'public' if prc.has_public_visibility else prc.certificate
        paca = PirogueAdminClientAdapter(prc.host, prc.port, prc.token, certificate)
        content = paca.get_packages_info()
    except RpcError as rpc_error:
        response['success'] = False
        response['grpc_success'] = True
        response['error'] = rpc_error.details()
    except Exception as exception:
        response['success'] = False
        response['grpc_success'] = False
        response['error'] = str(exception)
    else:
        response['success'] = True
        response['grpc_success'] = True
        response['content'] = content

    return response


def list_user_accesses(pirogue_credentials_id):
    prc = PiRogueCredentials.objects.get(pk=pirogue_credentials_id)

    response = dict({ "success": False, "grpc_success": False, "error": None })

    try:
        certificate = 'public' if prc.has_public_visibility else prc.certificate
        paca = PirogueAdminClientAdapter(prc.host, prc.port, prc.token, certificate)
        content = paca.list_user_accesses()
    except RpcError as rpc_error:
        response['success'] = False
        response['grpc_success'] = True
        response['error'] = rpc_error.details()
    except Exception as exception:
        response['success'] = False
        response['grpc_success'] = False
        response['error'] = str(exception)
    else:
        response['success'] = True
        response['grpc_success'] = True
        response['content'] = content

    return response


def create_user_access(pirogue_credentials_id):
    prc = PiRogueCredentials.objects.get(pk=pirogue_credentials_id)

    response = dict({ "success": False, "grpc_success": False, "error": None })

    try:
        certificate = 'public' if prc.has_public_visibility else prc.certificate
        paca = PirogueAdminClientAdapter(prc.host, prc.port, prc.token, certificate)
        content = paca.create_user_access()
    except RpcError as rpc_error:
        response['success'] = False
        response['grpc_success'] = True
        response['error'] = rpc_error.details()
    except Exception as exception:
        response['success'] = False
        response['grpc_success'] = False
        response['error'] = str(exception)
    else:
        response['success'] = True
        response['grpc_success'] = True
        response['content'] = content

    return response


def get_user_access(pirogue_credentials_id, idx):
    prc = PiRogueCredentials.objects.get(pk=pirogue_credentials_id)

    response = dict({ "success": False, "grpc_success": False, "error": None })

    try:
        certificate = 'public' if prc.has_public_visibility else prc.certificate
        paca = PirogueAdminClientAdapter(prc.host, prc.port, prc.token, certificate)
        content = paca.get_user_access(idx)
    except RpcError as rpc_error:
        response['success'] = False
        response['grpc_success'] = True
        response['error'] = rpc_error.details()
    except Exception as exception:
        response['success'] = False
        response['grpc_success'] = False
        response['error'] = str(exception)
    else:
        response['success'] = True
        response['grpc_success'] = True
        response['content'] = content

    return response


def reset_user_access_token(pirogue_credentials_id, idx):
    prc = PiRogueCredentials.objects.get(pk=pirogue_credentials_id)

    response = dict({ "success": False, "grpc_success": False, "error": None })

    try:
        certificate = 'public' if prc.has_public_visibility else prc.certificate
        paca = PirogueAdminClientAdapter(prc.host, prc.port, prc.token, certificate)
        content = paca.reset_user_access_token(idx)
    except RpcError as rpc_error:
        response['success'] = False
        response['grpc_success'] = True
        response['error'] = rpc_error.details()
    except Exception as exception:
        response['success'] = False
        response['grpc_success'] = False
        response['error'] = str(exception)
    else:
        response['success'] = True
        response['grpc_success'] = True
        response['content'] = content

    return response


def delete_user_access(pirogue_credentials_id, idx):
    prc = PiRogueCredentials.objects.get(pk=pirogue_credentials_id)

    response = dict({ "success": False, "grpc_success": False, "error": None })

    try:
        certificate = 'public' if prc.has_public_visibility else prc.certificate
        paca = PirogueAdminClientAdapter(prc.host, prc.port, prc.token, certificate)
        content = paca.delete_user_access(idx)
    except RpcError as rpc_error:
        response['success'] = False
        response['grpc_success'] = True
        response['error'] = rpc_error.details()
    except Exception as exception:
        response['success'] = False
        response['grpc_success'] = False
        response['error'] = str(exception)
    else:
        response['success'] = True
        response['grpc_success'] = True
        response['content'] = content

    return response


def set_user_access_permissions(pirogue_credentials_id, idx, permission_changes):
    prc = PiRogueCredentials.objects.get(pk=pirogue_credentials_id)

    response = dict({ "success": False, "grpc_success": False, "error": None })

    try:
        certificate = 'public' if prc.has_public_visibility else prc.certificate
        paca = PirogueAdminClientAdapter(prc.host, prc.port, prc.token, certificate)
        content = paca.set_user_access_permissions(idx, permission_changes)
    except RpcError as rpc_error:
        response['success'] = False
        response['grpc_success'] = True
        response['error'] = rpc_error.details()
    except Exception as exception:
        response['success'] = False
        response['grpc_success'] = False
        response['error'] = str(exception)
    else:
        response['success'] = True
        response['grpc_success'] = True
        response['content'] = content

    return response


def get_permission_list(pirogue_credentials_id):
    prc = PiRogueCredentials.objects.get(pk=pirogue_credentials_id)

    response = dict({ "success": False, "grpc_success": False, "error": None })

    try:
        certificate = 'public' if prc.has_public_visibility else prc.certificate
        paca = PirogueAdminClientAdapter(prc.host, prc.port, prc.token, certificate)
        content = paca.get_permission_list()
    except RpcError as rpc_error:
        response['success'] = False
        response['grpc_success'] = True
        response['error'] = rpc_error.details()
    except Exception as exception:
        response['success'] = False
        response['grpc_success'] = False
        response['error'] = str(exception)
    else:
        response['success'] = True
        response['grpc_success'] = True
        response['content'] = content

    return response


def add_device_monitoring(device_monitoring):
    pirogue_credentials_id = device_monitoring.pirogue.id

    monitoring_name = "-".join([
        str(device_monitoring.case.id)[:8],
        str(device_monitoring.device.id)[:8],
        str(device_monitoring.id)[:8]
    ])

    env = environ.FileAwareEnv()
    base_url = env('COLANDER_BASE_URL', default='http://192.168.1.34:8080')

    monitoring_config = {
        "enable": True,
        "url": base_url+reverse('api:network_events-ingest', kwargs={'pk':str(device_monitoring.id)}),
        "headers": {
            "X_AUTHENTICATION": f"Secret {device_monitoring.api_token.token}",
        },
        "mode": "periodic",
        "periodic_interval": 60,
        "periodic_rate": 20,
    }

    if device_monitoring.ip_filter:
        monitoring_config['filters'] = [
            { 'attribute': 'src_ip', 'values': [ str(device_monitoring.ip_filter) ] },
            { 'attribute': 'dst_ip', 'values': [ str(device_monitoring.ip_filter) ] },
        ]

    prc = PiRogueCredentials.objects.get(pk=pirogue_credentials_id)

    response = dict({ "success": False, "grpc_success": False, "error": None })

    try:
        certificate = 'public' if prc.has_public_visibility else prc.certificate
        paca = PirogueAdminClientAdapter(prc.host, prc.port, prc.token, certificate)
        content = paca.add_device_monitoring(monitoring_name, monitoring_config)
    except RpcError as rpc_error:
        response['success'] = False
        response['grpc_success'] = True
        response['error'] = rpc_error.details()
    except Exception as exception:
        response['success'] = False
        response['grpc_success'] = False
        response['error'] = str(exception)
    else:
        response['success'] = True
        response['grpc_success'] = True
        response['content'] = content

    return response


def delete_device_monitoring(device_monitoring):
    pirogue_credentials_id = device_monitoring.pirogue.id

    monitoring_name = "-".join([
        str(device_monitoring.case.id)[:8],
        str(device_monitoring.device.id)[:8],
        str(device_monitoring.id)[:8]
    ])

    prc = PiRogueCredentials.objects.get(pk=pirogue_credentials_id)

    response = dict({ "success": False, "grpc_success": False, "error": None })

    try:
        certificate = 'public' if prc.has_public_visibility else prc.certificate
        paca = PirogueAdminClientAdapter(prc.host, prc.port, prc.token, certificate)
        content = paca.delete_device_monitoring(monitoring_name)
    except RpcError as rpc_error:
        response['success'] = False
        response['grpc_success'] = True
        response['error'] = rpc_error.details()
    except Exception as exception:
        response['success'] = False
        response['grpc_success'] = False
        response['error'] = str(exception)
    else:
        response['success'] = True
        response['grpc_success'] = True
        response['content'] = content

    return response


def list_vpn_peers(pirogue_credentials_id):
    prc = PiRogueCredentials.objects.get(pk=pirogue_credentials_id)

    response = dict({ "success": False, "grpc_success": False, "error": None })

    try:
        certificate = 'public' if prc.has_public_visibility else prc.certificate
        paca = PirogueAdminClientAdapter(prc.host, prc.port, prc.token, certificate)
        content = paca.list_vpn_peers()
    except RpcError as rpc_error:
        response['success'] = False
        response['grpc_success'] = True
        response['error'] = rpc_error.details()
    except Exception as exception:
        response['success'] = False
        response['grpc_success'] = False
        response['error'] = str(exception)
    else:
        response['success'] = True
        response['grpc_success'] = True
        response['content'] = content

    return response


def add_vpn_peer(pirogue_credentials_id):
    prc = PiRogueCredentials.objects.get(pk=pirogue_credentials_id)

    response = dict({ "success": False, "grpc_success": False, "error": None })

    try:
        certificate = 'public' if prc.has_public_visibility else prc.certificate
        paca = PirogueAdminClientAdapter(prc.host, prc.port, prc.token, certificate)
        content = paca.add_vpn_peer()
    except RpcError as rpc_error:
        response['success'] = False
        response['grpc_success'] = True
        response['error'] = rpc_error.details()
    except Exception as exception:
        response['success'] = False
        response['grpc_success'] = False
        response['error'] = str(exception)
    else:
        response['success'] = True
        response['grpc_success'] = True
        response['content'] = content

    return response


def get_vpn_peer_config(pirogue_credentials_id, peer_idx:int):
    prc = PiRogueCredentials.objects.get(pk=pirogue_credentials_id)

    response = dict({ "success": False, "grpc_success": False, "error": None })

    try:
        certificate = 'public' if prc.has_public_visibility else prc.certificate
        paca = PirogueAdminClientAdapter(prc.host, prc.port, prc.token, certificate)
        content = paca.get_vpn_peer_config(peer_idx)
    except RpcError as rpc_error:
        response['success'] = False
        response['grpc_success'] = True
        response['error'] = rpc_error.details()
    except Exception as exception:
        response['success'] = False
        response['grpc_success'] = False
        response['error'] = str(exception)
    else:
        response['success'] = True
        response['grpc_success'] = True
        response['content'] = content

    return response


def delete_vpn_peer(pirogue_credentials_id, peer_idx:int):
    prc = PiRogueCredentials.objects.get(pk=pirogue_credentials_id)

    response = dict({ "success": False, "grpc_success": False, "error": None })

    try:
        certificate = 'public' if prc.has_public_visibility else prc.certificate
        paca = PirogueAdminClientAdapter(prc.host, prc.port, prc.token, certificate)
        content = paca.delete_vpn_peer(peer_idx)
    except RpcError as rpc_error:
        response['success'] = False
        response['grpc_success'] = True
        response['error'] = rpc_error.details()
    except Exception as exception:
        response['success'] = False
        response['grpc_success'] = False
        response['error'] = str(exception)
    else:
        response['success'] = True
        response['grpc_success'] = True
        response['content'] = content

    return response


def list_suricata_rules_sources(pirogue_credentials_id):
    prc = PiRogueCredentials.objects.get(pk=pirogue_credentials_id)

    response = dict({ "success": False, "grpc_success": False, "error": None })

    try:
        certificate = 'public' if prc.has_public_visibility else prc.certificate
        paca = PirogueAdminClientAdapter(prc.host, prc.port, prc.token, certificate)
        content = paca.list_suricata_rules_sources()
    except RpcError as rpc_error:
        response['success'] = False
        response['grpc_success'] = True
        response['error'] = rpc_error.details()
    except Exception as exception:
        response['success'] = False
        response['grpc_success'] = False
        response['error'] = str(exception)
    else:
        response['success'] = True
        response['grpc_success'] = True
        response['content'] = content

    return response


def add_suricata_rules_source(pirogue_credentials_id, name: str, url: str, params: Dict):
    prc = PiRogueCredentials.objects.get(pk=pirogue_credentials_id)

    response = dict({ "success": False, "grpc_success": False, "error": None })

    try:
        certificate = 'public' if prc.has_public_visibility else prc.certificate
        paca = PirogueAdminClientAdapter(prc.host, prc.port, prc.token, certificate)
        content = paca.add_suricata_rules_source(name, url, params)
    except RpcError as rpc_error:
        response['success'] = False
        response['grpc_success'] = True
        response['error'] = rpc_error.details()
    except Exception as exception:
        response['success'] = False
        response['grpc_success'] = False
        response['error'] = str(exception)
    else:
        response['success'] = True
        response['grpc_success'] = True
        response['content'] = content

    return response


def delete_suricata_rules_source(pirogue_credentials_id, name: str):
    prc = PiRogueCredentials.objects.get(pk=pirogue_credentials_id)

    response = dict({ "success": False, "grpc_success": False, "error": None })

    try:
        certificate = 'public' if prc.has_public_visibility else prc.certificate
        paca = PirogueAdminClientAdapter(prc.host, prc.port, prc.token, certificate)
        content = paca.delete_suricata_rules_source(name)
    except RpcError as rpc_error:
        response['success'] = False
        response['grpc_success'] = True
        response['error'] = rpc_error.details()
    except Exception as exception:
        response['success'] = False
        response['grpc_success'] = False
        response['error'] = str(exception)
    else:
        response['success'] = True
        response['grpc_success'] = True
        response['content'] = content

    return response
