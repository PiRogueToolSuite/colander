

import datetime

from django.core.files.base import ContentFile
from django.db.models.functions import Now
from django_q.models import Schedule
from django_q.tasks import async_task

from colander.core.archives.exporters.case import CaseArchiveExporter
from colander.core.models import ArchiveExport, Appendix
from colander.core.notifications import notify_case_archive_done
from colander.websocket.consumers import CaseContextConsumer

MISSING_ARCHIVE_EXPORTER_SCHEDULE_TASK_NAME = 'missing_archive_exporter'


def schedule_archive_export(archive_export:ArchiveExport):
    hook=f'{_archive_export_end.__module__}.{_archive_export_end.__qualname__}'
    async_task(_process_archive_export, str(archive_export.id), hook=hook)
    _ensure_missing_archives_task_exist()


def _process_archive_export(archive_export_id):
    print(f'Processing archive export: {archive_export_id}')

    archive_export = ArchiveExport.objects.get(pk=archive_export_id)
    if archive_export.type == Appendix.ExportType.CASE:
        cae = CaseArchiveExporter(archive_export.case)
        ct = ContentFile(cae.export(pretty=True), 'dummy.zip')
        archive_export.file = ct
        archive_export.save()


def _archive_export_end(task):
    archive_export_id = task.args[0]

    archive_export = ArchiveExport.objects.get(pk=archive_export_id)
    if task.success:
        archive_export.done_at = Now()
        archive_export.save()
        # Send notifications ...
        CaseContextConsumer.send_message_to_user_consumers(archive_export.case.owner, {
            'msg': 'A new archive is available',
            'detail': archive_export.filename,
        })
        notify_case_archive_done(archive_export)

    print("archive_export_done", archive_export_id, task.result)


def _ensure_missing_archives_task_exist():
    func=f'{_proceed_missing_archives.__module__}.{_proceed_missing_archives.__qualname__}'
    print('scheduled func to call:', func)
    if Schedule.objects.filter(func=func).exists(): return
    print('creating scheduled func to call:', func)
    Schedule.objects.create(func=func, schedule_type='H', name=MISSING_ARCHIVE_EXPORTER_SCHEDULE_TASK_NAME)


def _proceed_missing_archives():
    unprocessed_archive_exports = ArchiveExport.objects.filter(
        done_at__isnull=True,
        requested_at__lt=Now() - datetime.timedelta(hours=1)
        ).order_by('-requested_at').all()

    for archive_export_to_process in unprocessed_archive_exports:
        schedule_archive_export(archive_export_to_process)

    unprocessed_archive_exports_count = ArchiveExport.objects.filter(
        done_at__isnull=True,
        ).count()

    if unprocessed_archive_exports_count > 0:
        return

    # unschedule 'missing_archive_exporter' task
    func=f'{_proceed_missing_archives.__module__}.{_proceed_missing_archives.__qualname__}'
    if Schedule.objects.filter(func=func).exists():
        print('unscheduling func:', func)
        Schedule.objects.get(func=func).delete()
