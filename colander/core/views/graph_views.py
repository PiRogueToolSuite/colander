from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def graph_base_view(request):
    # active_case = get_active_case(request, case_id)
    #
    # if active_case is None:
    #     messages.add_message(
    #         request, messages.WARNING,
    #         "In order to graph a case, you must first select a case to work on"
    #     )
    #     return redirect('case_create_view')
    #
    # ctx = {
    #     "active_case": active_case
    # }
    # return render(request, 'pages/graph/base.html', context=ctx)
    return render(request, 'pages/graph/base.html')
