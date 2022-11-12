from colander.core.models import Case


def active_case(request):
    active_case = None
    user_cases = []
    if request.user:
        user_cases = Case.get_user_cases(request.user)
        request.user_cases = user_cases
        if 'active_case' in request.session:
            try:
                active_case = Case.objects.get(id=request.session['active_case'])
                request.active_case = active_case
            except Exception:
                pass

    return {
        'active_case': active_case,
        'user_cases': user_cases,
    }
