import traceback

import grpc
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django_q.models import Schedule
from grpc import RpcError
from pirogue_admin_client import PirogueAdminClientAdapter

from colander.core.models import PiRogueCredentials, PiRogueStatus


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


def _proceed_pirogue_status_retrieval(pirogue_credentials_id):

    prc = None
    try:
        prc = PiRogueCredentials.objects.get(pk=pirogue_credentials_id)
    except PiRogueCredentials.DoesNotExist:
        unschedule_pirogue_status_retrieval(pirogue_credentials_id)
        return

    ps = PiRogueStatus.objects.create(pirogue_credentials=prc)

    try:
        certificate = 'public' if prc.has_public_visibility else prc.certificate
        paca = PirogueAdminClientAdapter(prc.host, prc.port, prc.token, certificate)
        status = paca.get_status()
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
    except Exception as exception:
        ps.success = False
        ps.error = str(exception)
        ps.save()
    else:
        ps.success = True
        ps.content = status
        ps.save()


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
