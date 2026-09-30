from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView

from colander.core.forms import CommentForm
from colander.core.models import Comment
from colander.core.utils import safe_redirect_to_referrer, safe_get_referrer


@login_required
def create_comment_view(request):
    owner = request.user
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            if not hasattr(comment, 'owner'):
                comment.owner = owner
            comment.save()
            form.save_m2m()

    return safe_redirect_to_referrer(request)


class CommentUpdateView(LoginRequiredMixin, UpdateView):
    model = Comment
    template_name = ''
    fields = [
        'content'
    ]

    def get_success_url(self):
        return safe_get_referrer(self.request)

@login_required
def edit_comment_view(request, pk):
    owner = request.user
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.owner = owner
            comment.save()
            form.save_m2m()

    return safe_redirect_to_referrer(request)


@login_required
def delete_comment_view(request, pk):
    comment = Comment.objects.get(id=pk)
    comment.delete()

    return safe_redirect_to_referrer(request)

