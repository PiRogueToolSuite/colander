from django.shortcuts import redirect

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
    }
