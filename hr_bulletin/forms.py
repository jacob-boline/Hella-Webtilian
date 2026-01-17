# hr_bulletin/forms.py

from django import forms
from hr_bulletin.models import Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = [
            "title",
            "slug",
            "body",
            "hero",
            "status",
            "publish_at",
            "pin_until",
            "tags",
            "allow_comments",
        ]
        widgets = {
            "publish_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "pin_until":  forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }
