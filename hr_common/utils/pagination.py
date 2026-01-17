# hr_common/utils/pagination.py

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def paginate(request, qs, per_page=10):
    """
    Generic pagination helper.

    Returns a `page_obj` you can pass to templates, with:
      - page_obj.object_list
      - page_obj.has_next(), has_previous(), etc.
    """
    page = request.GET.get("page", 1)
    paginator = Paginator(qs, per_page)

    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    return page_obj
