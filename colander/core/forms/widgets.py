from django.forms.widgets import ClearableFileInput


class ThumbnailFileInput(ClearableFileInput):
    template_name = "forms/widgets/thumbnail_input_file.html"
    thumbnail_url = None

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget'].update(dict(thumbnail_url=self.thumbnail_url))
        return context
