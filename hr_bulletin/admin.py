# hr_bulletin/admin.py

from django.contrib import admin
from django.contrib.admin import ModelAdmin

from hr_bulletin.models import Post, Tag


@admin.register(Post)
class PostAdmin(ModelAdmin):
    list_display = ("id", "title", "slug", "hero", "status", "author", "body", "publish_at", "created_at", "updated_at", "pin_until", "allow_comments")
    list_editable = ("title", "hero", "status", "pin_until", "allow_comments", "body")
    readonly_fields = (
        "slug",
        "author",
        "publish_at",
        "created_at",
        "updated_at",
    )
    list_filter = ("tags", "status", "author")


@admin.register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ("id", "name", "slug")
    list_editable = ("name",)
    readonly_fields = ("slug",)
