from django.conf import settings
from django.http import HttpResponseForbidden

from colander.core.forms import DocumentationForm
from colander.core.models import Case

class GitCommitHashMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        try:  # this attribute does not exist in dev mode
            request.GIT_COMMIT_HASH = settings.GIT_COMMIT_HASH
        except: pass


class ContextualCaseMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.user is None or not request.user.is_authenticated:
            return

        workspace_case_id = view_kwargs.pop('case_id', None)
        if workspace_case_id is None:
            return

        case = Case.objects.get(pk=workspace_case_id)
        if case and case.can_contribute(request.user):
            request.contextual_case = case  # even if case is None
        else:
            return HttpResponseForbidden()



def contextual_case(request):
    ctx_case = None
    user_cases = []
    if request.user and request.user.is_authenticated:
        user_cases = Case.get_user_cases(request.user)
        request.user_cases = user_cases
        if hasattr(request, 'contextual_case'):
            ctx_case = request.contextual_case
            if ctx_case and ctx_case.can_contribute(request.user):
                request.documentation_form = DocumentationForm(initial={'documentation': ctx_case.documentation})
            else:
                ctx_case = None

    return {
        'contextual_case': ctx_case,
        'user_cases': user_cases,
        'cyberchef_base_url': settings.CYBERCHEF_BASE_URL,
    }
