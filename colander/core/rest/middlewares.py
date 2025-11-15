import logging

from django.core.exceptions import ValidationError
from rest_framework import permissions

from colander.core.models import Case

logger = logging.getLogger(__name__)


def get_case_from_request(request):
    """
    Resolve a `Case` instance from a Django REST `request`.

    The function looks for a case identifier in multiple places (in order of precedence):
    1. `request.data["case_id"]`
    2. HTTP header `"X-ColanderCase"`
    3. `request.active_case`
    4. `request.contextual_case`

    If `request.active_case` or `request.contextual_case` are already `Case` instances,
    their `.id` is used. If a `case_id` is found and a `request.user` exists, the method
    attempts to fetch the `Case` from the database. The code currently converts the
    resolved `case_id` to `str` and appends the character `'e'` before lookup.

    Returns:
        Case or None: The `Case` instance if found and the user is allowed to contribute,
        otherwise `None`.

    Notes:
        - Any `Case.DoesNotExist`, `ValidationError`, or other exceptions during lookup
          result in `None` being returned.
        - If the found case exists but `case.can_contribute(user)` is false, the function
          logs an error and returns `None`.
    """
    case_id = request.data.get("case_id", None)
    case_context = getattr(request, "contextual_case", None)
    if isinstance(case_context, Case):
        case_context = case_context.id
    case_active = getattr(request, "active_case", None)
    if isinstance(case_active, Case):
        case_active = case_active.id
    case_header = request.headers.get("X-ColanderCase", None)
    case_id = case_id or case_header or case_active or case_context or None

    user = request.user

    logger.debug(f"Case id: {case_id}, user: {user}")

    if not case_id or not user:
        return None

    try:
        case = Case.objects.get(id=str(case_id))
    except (Case.DoesNotExist, ValidationError, Exception):
        return None

    if not case.can_contribute(user):
        logger.error(f"User {user} is not authorized to contribute to case {case_id}")
        return None

    return case


class CanContributeToCase(permissions.BasePermission):
    """
    Permission class for DRF that authorizes access only if the requesting user
    can contribute to the resolved `Case`.

    This permission resolves the case using `get_case_from_request` and then calls
    `case.can_contribute(request.user)` to determine permission.
    """
    message = 'Unauthorized.'

    def has_permission(self, request, view):
        """
        Determine whether `request.user` has contribute permissions on the resolved case.

        Returns:
            bool: True if the case exists and `case.can_contribute(request.user)` is True,
            otherwise False.
        """
        logger.info(request.data)
        case = get_case_from_request(request)
        if not case:
            return False
        return case.can_contribute(request.user)


class OwnCase(permissions.BasePermission):
    """
    Permission class for DRF that authorizes access only if the requesting user
    is the owner of the resolved `Case`.
    """
    message = 'Unauthorized.'

    def has_permission(self, request, view):
        """
        Determine whether `request.user` is the owner of the resolved case.

        Returns:
            bool: True if the case exists and `case.owner == request.user`, otherwise False.
        """
        case = get_case_from_request(request)
        if not case:
            return False
        return case.owner == request.user
