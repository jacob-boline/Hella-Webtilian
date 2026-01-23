# hr_bulletin/views.py

import logging

from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_GET

from hr_access.permissions import is_site_admin
from hr_bulletin.models import Post
from hr_common.utils.pagination import paginate
from hr_common.utils.unified_logging import log_event

logger = logging.getLogger(__name__)


@require_GET
def bulletin_list(request):
    qs = Post.objects.frontpage()
    page_obj = paginate(request, qs, per_page=10)
    log_event(
        logger,
        logging.INFO,
        "bulletin.list.rendered",
        page_number=page_obj.number,
        total_count=page_obj.paginator.count,
    )
    ctx = {"page_obj": page_obj, "posts": page_obj.object_list}
    return render(request, "hr_bulletin/list.html", ctx)


@require_GET
def bulletin_list_partial(request):
    page_number = request.GET.get("page", 1)

    paginator = Paginator(Post.objects.frontpage(), 3)
    page_obj = paginator.get_page(page_number)

    log_event(
        logger,
        logging.INFO,
        "bulletin.list_partial.rendered",
        page_number=page_obj.number,
        total_count=paginator.count,
    )

    ctx = {"page_obj": page_obj, "posts": page_obj.object_list}
    resp = render(request, "hr_bulletin/_list.html", ctx)

    # Tell the client what to load next (stable sentinel pattern)
    if page_obj.has_next():
        resp["X-Next-Page"] = str(page_obj.next_page_number())
    # else: no header => client removes sentinel / stops

    return resp


@require_GET
def bulletin_detail(request, slug):
    preview = request.GET.get("preview") in ("1", "true", "yes")
    now = timezone.now()

    if preview and is_site_admin(request.user):
        post = get_object_or_404(Post, slug=slug)  # any status
        log_event(
            logger,
            logging.INFO,
            "bulletin.detail.preview_rendered",
            slug=slug,
            post_id=post.id,
        )
    else:
        # published & released
        post = get_object_or_404(
            Post.objects.filter(slug=slug, status="published").filter(publish_at__isnull=True)
            | Post.objects.filter(slug=slug, status="published", publish_at__lte=now)
        )
        log_event(
            logger,
            logging.INFO,
            "bulletin.detail.rendered",
            slug=slug,
            post_id=post.id,
        )

    return render(request, "hr_bulletin/detail.html", {"post": post})



# # ------------------------------------------------------------------ #
# # Helpers
# # ------------------------------------------------------------------ #
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
