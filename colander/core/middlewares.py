from django.conf import settings

from colander.core.forms import DocumentationForm
from colander.core.models import Case


class ActiveCaseMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        response = self.get_response(request)
        return response

    # def process_view(self, request, view_func, view_args, view_kwargs):
    #     print(view_func)
    #     if not request.session.get('active_case'):
    #         return redirect('collect_case_create_view')


class ContextualCaseMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        print('__call__', 'before')
        response = self.get_response(request)
        print('__call__', 'after')
        return response
        # print('__call__', 'Nueeee')
        # if hasattr(request, 'contextual_case'):
        #     response.context_data = {'active_case': request.contextual_case}
        # else:
        #     response.context_data = {'active_case': None}
        # return self.process_template_response(request, response)

    def process_view(self, request, view_func, view_args, view_kwargs):
        print('process_view', 'start', request)
        print('process_view', 'start', view_func)
        print('process_view', 'start', view_args)
        print('process_view', 'start', view_kwargs)
        if request.user is None:
            print('process_view', 'no user')
            return

        workspace_case_id = view_kwargs.pop('case_id', None)
        if workspace_case_id is None:
            print('process_view', 'no context')
            return

        print('process_view', 'user', request.user)
        case = Case.objects.get(pk=workspace_case_id)
        if case is None:
            print('process_view', 'contextual_case not found', workspace_case_id)
        else:
            print('process_view', 'case', case)
            if case.can_contribute(request.user):
                request.contextual_case = case  # even if case is None
            else:
                print('process_view', 'user', request.user, 'cannot contribute to case', case)

        print('process_view', 'end', request.contextual_case)


def contextual_case(request):
    ctx_case = None
    user_cases = []
    if request.user and request.user.is_authenticated:
        user_cases = Case.get_user_cases(request.user)
        request.user_cases = user_cases
        if hasattr(request, 'contextual_case'):
            ctx_case = request.contextual_case
            request.documentation_form = DocumentationForm(initial={'documentation': ctx_case.documentation})

    return {
        'contextual_case': ctx_case,
        'user_cases': user_cases,
        'cyberchef_base_url': settings.CYBERCHEF_BASE_URL,
    }


def active_case(request):
    active_case = None
    user_cases = []
    if request.user and request.user.is_authenticated:
        user_cases = Case.get_user_cases(request.user)
        request.user_cases = user_cases
        if 'active_case' in request.session:
            try:
                active_case = Case.objects.get(id=request.session['active_case'])
                request.active_case = active_case
                request.documentation_form = DocumentationForm(initial={'documentation': active_case.documentation})
            except Exception:
                pass

    return {
        'active_case': active_case,
        'user_cases': user_cases,
        'cyberchef_base_url': settings.CYBERCHEF_BASE_URL,
    }
