from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from contextvars import ContextVar
from django.http import Http404

import logging
logger = logging.getLogger(__name__)

_current_request = ContextVar("current_request", default=None)


def set_current_request(request):
    return _current_request.set(request)

def get_current_request():
    return _current_request.get()

def reset_current_request():
    _current_request.set(None)


class ModelGuardianMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        set_current_request(request)
        response = self.get_response(request)
        reset_current_request() # important due to pytest same context
        return response

    def process_exception(self, request, exception):
        if isinstance(exception, ObjectDoesNotExist):
            raise Http404("Requested resource was not found.")
        return None


class ModelGuardianManager(models.Manager):

    def get(self, *args, **kwargs):
        logger.info(f"get({self.model}, ...)")
        return self.get_queryset().get(*args, **kwargs)

    def unguarded_get(self, *args, **kwargs):
        logger.info(f"unguarded_get({self.model}, ...)")
        return self.get_queryset(guarded=False).get(*args, **kwargs)

    def get_queryset(self, guarded:bool=True):
        logger.info(f"get_queryset({self.model}, guarded:{guarded})")
        enforced_qs = models.QuerySet(model=self.model, using=self._db, hints=self._hints)

        request = get_current_request()

        if request is None:
            logger.info(f"No request available")
            # Internal call
            return enforced_qs

        logger.info(f"Request available")
        if not guarded:
            logger.info(f"Disabled guard for sub-sequence call")
            request.not_guarded_subsequence = True
            return enforced_qs

        if hasattr(request, "not_guarded_subsequence") and request.not_guarded_subsequence:
            logger.info(f"Disabled guard for sub-sequence call")
            guarded = False
            return enforced_qs

        if hasattr(request, "contextual_case"):
            logger.info(f"request.contextual_case: {request.contextual_case}")
            if hasattr(self.model, 'case'):
                logger.info(f"Enforcing guard against contextual case")
                enforced_qs = enforced_qs.filter(case=request.contextual_case)

        if hasattr(request, "user"):
            logger.info(f"request.user: {request.user} guarded_access: {guarded}")
            if request.user.is_superuser:
                logger.info(f"Supervisor access")
                return enforced_qs
            if request.user.is_anonymous:
                logger.warning(f"Guarded anonymous access. Blocked !")
                raise ObjectDoesNotExist()
            else:
                if hasattr(self.model, 'case'):
                    logger.info(f"Enforcing guard against case contributors")
                    enforced_qs = enforced_qs.filter(case__in=request.user.all_my_cases)
                elif hasattr(self.model, 'owner'):
                    logger.info(f"Enforcing guard against entity ownership")
                    enforced_qs = enforced_qs.filter(owner=request.user)

        return enforced_qs
