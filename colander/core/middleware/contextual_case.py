from colander.core.models import Case


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
        #view_kwargs.pop('case_id')
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

        print('process_view', 'end')

    def process_template_response(self, request, response):
        print('process_template_response', response.context_data)
        return response
