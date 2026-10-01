import json
import traceback

from django.core.mail import EmailMultiAlternatives
from django.core.serializers.json import DjangoJSONEncoder
from django.forms import model_to_dict
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string
from django.urls import reverse
from django.db.models.functions import Now
from django.utils.html import strip_tags
from django_q.tasks import async_task

import environ

from colander.core.models import NotificationMessage, Appendix, ArchiveExport

import logging
logger = logging.getLogger(__name__)

def notification_message_task(notification_message_id:str):
    nm = NotificationMessage.objects.get(id=notification_message_id)

    try:
        if nm.type == Appendix.NotificationType.MAIL:
            notification_message_mail(nm)
        nm.success = True
    finally:
        nm.processed_at = Now()
        nm.save()


def notify_case_archive_done(archive_export: ArchiveExport):
    try:
        env = environ.FileAwareEnv()
        base_url = env('COLANDER_BASE_URL', default='http://localhost:8080')

        ctx = dict()

        # model_to_dict: a quick way to dump model as dist with exclude feature
        #                but contains objects like UUID() and datetime,
        #                which are not serializable as this
        # json.dumps with DjangoJSONEncoder: serialize all django 'objects' as str
        # json.loads: get back json object to by stored in database

        ctx['case'] = json.loads(json.dumps(model_to_dict(archive_export.case, exclude=['teams']), cls=DjangoJSONEncoder))
        ctx['user'] = json.loads(json.dumps(model_to_dict(archive_export.case.owner, exclude=['password']), cls=DjangoJSONEncoder))
        ctx['subject'] = "A new archive is available"
        ctx['url'] = f"{base_url}{archive_export.case.get_absolute_url()}"

        nm = NotificationMessage.objects.create(
            template_path='notification/case-archive-done',
            type=Appendix.NotificationType.MAIL,
            recipient=archive_export.case.owner,
            context=ctx,
        )
        nm.save()

        return async_task(notification_message_task, str(nm.id))
    except Exception as e:
        logger.error("can't create case archive done notification, traceback = ",
                     exc_info=e)


def notification_message_mail(notification_message: NotificationMessage):
    txt_part = None
    html_part = None

    try:
        html_part = render_to_string(
            f'{notification_message.template_path}.html.tpl',
            context=notification_message.context,
        )
    except TemplateDoesNotExist as tdne:
        logger.warning('Template not found: %s.html.tpl',
                       notification_message.template_path,
                       exc_info=tdne)

    try:
        txt_part = render_to_string(
            f'{notification_message.template_path}.txt.tpl',
            context=notification_message.context,
        )
    except TemplateDoesNotExist as tdne:
        logger.warning('Template not found: %s.txt.tpl',
                       notification_message.template_path,
                       exc_info=tdne)


    if txt_part is None and html_part is None:
        logger.warning('No content to produce without template')
        return

    if txt_part is None:
        txt_part = strip_tags(html_part)

    logger.debug('txt_part: %s', txt_part)
    logger.debug('html_part: %s', html_part)

    if notification_message.recipient.email is None:
        logger.warning('No email address to send to')
        return

    mail = EmailMultiAlternatives(
        subject = notification_message.context['subject'],
        body = txt_part,
        to = [ notification_message.recipient.email ],
    )

    if html_part is not None:
        mail.attach_alternative(html_part, 'text/html')

    mail.send()
