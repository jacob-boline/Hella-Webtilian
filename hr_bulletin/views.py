# hr_bulletin/views.py

from typing import Dict, Any

# from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import Http404, HttpResponseBadRequest, JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods

# from hr_access.models import User

# from .forms import PostForm
from hr_bulletin.models import Post
from hr_core.utils.pagination import paginate
from hr_core.utils.permissions import is_site_admin


@require_GET
def bulletin_list(request):
    qs = Post.objects.frontpage()
    page_obj = paginate(request, qs, per_page=10)
    ctx = {"page_obj": page_obj, "posts": page_obj.object_list}
    return render(request, "hr_bulletin/list.html", ctx)


@require_GET
def bulletin_list_partial(request):
    qs = Post.objects.frontpage()
    page_obj = paginate(request, qs, per_page=10)
    ctx = {"page_obj": page_obj, "posts": page_obj.object_list}
    return render(request, "hr_bulletin/_list.html", ctx)


@require_GET
def bulletin_detail(request, slug):
    preview = request.GET.get("preview") in ("1", "true", "yes")
    now = timezone.now()

    if preview and is_site_admin(request.user):
        post = get_object_or_404(Post, slug=slug)  # any status
    else:
        # published & released
        post = get_object_or_404(
            Post.objects.filter(slug=slug, status="published").filter(publish_at__isnull=True)
            | Post.objects.filter(slug=slug, status="published", publish_at__lte=now)
        )

    return render(request, "hr_bulletin/detail.html", {"post": post})


#
# # -------------------------------------------------------------------
# # Helpers
# # -------------------------------------------------------------------
#
# def _is_site_admin(user) -> bool:
#     """Allow superusers or users in the 'Site admin' group (or custom property)."""
#     if not getattr(user, "is_authenticated", False):
#         return False
#
#     if getattr(user, "is_superuser", False):
#         return True
#
#         # your custom property on hr_access.User
#     if bool(getattr(user, "is_site_admin", False)):
#         return True
#
#         # fallback: check group membership (guarded)
#     try:
#         return user.groups.filter(name="Site admin").exists()
#     except Group.DoesNotExist:
#         return False
#
#
# def staff_or_site_admin_required(view):
#     return login_required(user_passes_test(_is_site_admin)(view))
#
#
# def _paginate(request, qs, per_page=10):
#     page = request.GET.get('page', 1)
#     paginator = Paginator(qs, per_page)
#     try:
#         page_obj = paginator.page(page)
#     except PageNotAnInteger:
#         page_obj = paginator.page(1)
#     except EmptyPage:
#         page_obj = paginator.page(paginator.num_pages)
#     return page_obj
#
#
# def _published_qs():
#     now = timezone.now()
#     return Post.objects.filter(status='published').filter(publish_at__isnull=True) | Post.objects.filter(status='published', publish_at__lte=now)
#
#
# def _frontpage_qs():
#     """
#     Public list: published & released. Uses Post.Meta ordering:
#     ['-pin_until','-publish_at','-created_at'].
#     """
#     now = timezone.now()
#     base = Post.objects.filter(status='published')
#     qs = base.filter(publish_at__isnull=True) | base.filter(publish_at__lte=now)
#     return qs.order_by(*Post._meta.ordering)
#
#    # return Post.objects.filter(status='published').filter(publish_at__isnull=True) | Post.objects.filter(status='published', publish_at__lte=now).order_by(*Post._meta.ordering)
#
#
# def _serialize_post(post: Post) -> Dict[str, Any]:
#     return {
#         "title":          post.title,
#         "slug":           post.slug,
#         "body":           post.body,  # you may want to strip/shorten for list API
#         "hero":           post.hero.url if post.hero else None,
#         "status":         post.status,
#         "publish_at":     post.publish_at.isoformat() if post.publish_at else None,
#         "updated_at":     post.updated_at.isoformat() if post.updated_at else None,
#         "created_at":     post.created_at.isoformat() if post.created_at else None,
#         "pin_until":      post.pin_until.isoformat() if post.pin_until else None,
#         "allow_comments": post.allow_comments,
#         "tags":           [t.slug for t in post.tags.all()],
#     }
#
#
# # -------------------------------------------------------------------
# # Public: SSR container (infinite scroll shell)
# # GET /bulletin/
# # -------------------------------------------------------------------
#
#
# @require_GET
# def bulletin_list(request):
#     qs = _frontpage_qs()
#     page_obj = _paginate(request, qs, per_page=10)
#     ctx = {"page_obj": page_obj, "posts": page_obj.object_list}
#     return render(request, "hr_bulletin/list.html", ctx)
#
# # -------------------------------------------------------------------
# # HTMX partial list (page=n)
# # GET /bulletin/partial/list?page=n
# # -------------------------------------------------------------------
#
#
# @require_GET
# def bulletin_list_partial(request):
#     qs = _frontpage_qs()
#     page_obj = _paginate(request, qs, per_page=10)
#     ctx = {"page_obj": page_obj, "posts": page_obj.object_list}
#     return render(request, "hr_bulletin/partials/list.html", ctx)
#
# # -------------------------------------------------------------------
# # JSON list (page=n)
# # GET /api/bulletin/posts?page=n
# # -------------------------------------------------------------------
#
#
# @require_GET
# def api_bulletin_posts(request):
#     qs = _frontpage_qs()
#     page_obj = _paginate(request, qs, per_page=10)
#     data = [_serialize_post(p) for p in page_obj.object_list]
#     return JsonResponse(
#         {
#             "count":     page_obj.paginator.count,
#             "num_pages": page_obj.paginator.num_pages,
#             "page":      page_obj.number,
#             "results":   data,
#         },
#         status=200,
#     )
#
# # -------------------------------------------------------------------
# # Public detail (staff can preview drafts via ?preview=1)
# # GET /bulletin/<slug>/
# # -------------------------------------------------------------------
#
#
# @require_GET
# def bulletin_detail(request, slug):
#     preview = request.GET.get("preview") in ("1", "true", "yes")
#     now = timezone.now()
#
#     if preview and _is_site_admin(request.user):
#         post = get_object_or_404(Post, slug=slug)  # any status
#     else:
#         # published & released
#         post = get_object_or_404(
#             Post.objects.filter(slug=slug, status="published").filter(publish_at__isnull=True)
#             | Post.objects.filter(slug=slug, status="published", publish_at__lte=now)
#         )
#
#     return render(request, "hr_bulletin/detail.html", {"post": post})
