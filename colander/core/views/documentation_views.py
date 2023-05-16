from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.contrib import messages

from colander.core.views.views import get_active_case


@login_required
def write_documentation_view(request):
    active_case = get_active_case(request)
    if not active_case:
        messages.add_message(request, messages.WARNING,
                             "In order to write case documentation, you must first select a case to work on")
        return redirect('case_create_view')

    return render(request,
                  'pages/document/base.html')
