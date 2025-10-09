from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render


@login_required
def import_view(request):
    active_case = request.contextual_case
    if not active_case:
        return redirect('case_create_view')
    ctx = {
        'active_case': active_case,
    }
    return render(request, 'pages/import/base.html', context=ctx)


@login_required
def import_misp_view(request):
    active_case = request.contextual_case
    if not active_case:
        return redirect('case_create_view')

    if request.method == 'POST':
        pass

    ctx = {
        'active_case': active_case,
    }
    return render(request, 'import/misp.html', context=ctx)
