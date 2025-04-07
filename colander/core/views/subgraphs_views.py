from django.conf.urls.static import static
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.staticfiles import finders
from django.forms import ModelForm
from django.http import StreamingHttpResponse, HttpResponse
from django.shortcuts import redirect, render
from django.views.generic import CreateView, UpdateView

from colander.core.models import SubGraph
from colander.core.views.views import CaseContextMixin


class SubGraphForm(ModelForm):
    class Meta:
        model = SubGraph
        fields = [
            'name',
            'description',
        ]

    @staticmethod
    def get_custom_form(user, case, data=None):

        if data is None:
            data = dict()

        data['case'] = str(case.id)
        data['owner'] = str(user.id)
        form = SubGraphForm(data)
        return form


class SubGraphCreateView(LoginRequiredMixin, CaseContextMixin, CreateView):
    model = SubGraph
    template_name = 'pages/graph/subgraphs.html'
    fields = [
        'name',
        'description',
    ]
    contextual_success_url = 'subgraph_create_view'
    case_required_message_action = "create subgraph"

    def get_form(self, form_class=None, edit=False):
        form = super(SubGraphCreateView, self).get_form(form_class)

        if not edit:
            form.initial['case'] = self.active_case
            form.initial['owner'] = self.request.user

        return form

    def form_valid(self, form):
        if form.is_valid() and self.active_case:
            subgraph = form.save(commit=False)
            if not hasattr(subgraph, 'owner'):
                subgraph.owner = self.request.user
                subgraph.case = self.active_case
            subgraph.save()
            form.save_m2m()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        #ctx['devices'] = Device.get_user_devices(self.request.user, self.active_case)
        ctx['subgraphs'] = (SubGraph.objects.filter(owner=self.request.user, case=self.active_case)
                            .order_by('name'))
        ctx['pinned_subgraphs'] = (SubGraph.get_pinned(user=self.request.user, case=self.active_case)
                                   .order_by('created_at'))
        ctx['is_editing'] = False
        return ctx


class SubGraphUpdateView(SubGraphCreateView, UpdateView):
    case_required_message_action = "update subgraph"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['is_editing'] = True
        return ctx

    def get_form(self, form_class=None):
        return super().get_form(form_class, True)


@login_required
def delete_subgraph_view(request, pk):
    obj = SubGraph.objects.get(id=pk)
    obj.delete()
    return redirect("subgraph_create_view", case_id=request.contextual_case.id)


@login_required
def subgraph_editor_view(request, pk):
    obj = SubGraph.objects.get(id=pk)
    ctx = {
        'subgraph': obj,
        'pinned_subgraphs': (SubGraph.get_pinned(user=request.user, case=request.contextual_case)
                             .order_by('created_at')),
    }
    return render(request, 'pages/graph/subgraph.html', context=ctx)


@login_required
def subgraph_pin_toggle_view(request, pk):
    return redirect("subgraph_create_view", case_id=request.contextual_case.id)


@login_required
def subgraph_thumbnail_view(request, pk):
    content = SubGraph.objects.get(id=pk)
    if content.thumbnail:
        response = StreamingHttpResponse(content.thumbnail, content_type='image/png')
        return response
    else:
        image = finders.find('images/no-thumbnail-yet-256x144.png')
        with open(image, "rb") as f:
            response = HttpResponse(f.read(), content_type="image/png")
            return response
