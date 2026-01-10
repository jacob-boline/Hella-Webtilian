# hr_live/views.py

from typing import Dict, Any
import logging

from django.shortcuts import render
from django.utils import timezone

from hr_core.utils.pagination import paginate
from hr_live.unified_logging import log_event
from hr_live.models import Show

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------


def _get_today():
    return timezone.localdate()


def _serialize_show(show: Show) -> Dict[str, Any]:
    """
    JSON representation of a show that matches your model.
    """
    lineup_names = [act.name for act in show.lineup.all()]

    return {
        'slug': show.slug,
        'title': show.title,
        'subtitle': show.subtitle,
        'status': show.status,
        'date': show.date.isoformat() if show.date else None,
        'time': show.time.isoformat() if show.time else None,
        'timezone': show.timezone,
        'venue': show.venue.name if show.venue_id else None,
        'booker': f"{show.booker.first_name} {show.booker.last_name}".strip() if show.booker_id else None,
        'lineup': lineup_names,
        'image': show.image.url if show.image else None,
        'readable_details': show.readable_details,
    }


# -------------------------------------------------------------------
# SSR: /live/ — upcoming shows list
# -------------------------------------------------------------------

def live_upcoming_list(request):
    qs = Show.objects.upcoming()
    page_obj = paginate(request, qs, per_page=10)
    log_event(
        logger,
        logging.INFO,
        "live.upcoming_list.rendered",
        page_number=page_obj.number,
        total_count=page_obj.paginator.count,
    )

    context = {
        'page_obj': page_obj,
        'shows': page_obj.object_list
    }

    return render(request, 'hr_live/upcoming_list.html', context)


# -------------------------------------------------------------------
# SSR: /live/past/ — archive
# -------------------------------------------------------------------

def live_past_list(request):
    qs = Show.objects.past()
    page_obj = paginate(request, qs, per_page=10)
    log_event(
        logger,
        logging.INFO,
        "live.past_list.rendered",
        page_number=page_obj.number,
        total_count=page_obj.paginator.count,
    )

    context = {
        'page_obj': page_obj,
        'shows': page_obj.object_list,
    }

    return render(request, 'hr_live/past_list.html', context)

# ---------------------------------------------------------------------------------------------------#
#                        BELOW IS NOT FOR MVP - COMMENTED UNTIL NEEDED                               #
# ---------------------------------------------------------------------------------------------------#

#
# # -------------------------------------------------------------------
# # HTMX: /live/partial/list?page=n
# # -------------------------------------------------------------------
#
# def live_upcoming_partial(request):
#     qs = Show.objects.upcoming()
#     page_obj = _paginate(request, qs, per_page=10)
#
#     context = {
#         'page_obj': page_obj,
#         'shows': page_obj.object_list,
#     }
#
#     return render(request, 'hr_live/partials/upcoming_list.html', context)
#
#
# # -------------------------------------------------------------------
# # JSON: /api/live/shows?status=published&after=today
# # -------------------------------------------------------------------
# def api_live_shows_list(request):
#     status = request.GET.get('status', None)
#     after = request.GET.get('after')
#
#     qs = Show.objects.all()
#
#     if status:
#         qs = qs.filter(status=status)
#
#     if after:
#         if after == 'today':
#             dt = _get_today()
#         else:
#             try:
#                 dt = datetime.strptime(after,'%Y-%m-%d').date()
#             except ValueError:
#                 return JsonResponse(
#                     {'error': "Invalid 'after' date. Use 'today' or YYYY-MM-DD."},
#                     status=400
#                 )
#         qs = qs.filter(date__gte=dt)
#
#     qs = qs.order_by('date', 'time', 'id')
#
#     data = [_serialize_show(show) for show in qs]
#     return JsonResponse({'results': data}, status=200)
#
#
# # -------------------------------------------------------------------
# # iCal: /live/calendar.ics — all upcoming shows
# # -------------------------------------------------------------------
#
# def live_calendar_ics(request):
#     qs = Show.objects.upcoming()
#
#     lines = [
#         'BEGIN:VCALENDAR',
#         'VERSION:2.0',
#         'PRODID:-//Hella Reptilian//Live Shows//EN',
#     ]
#
#     now = timezone.now()
#     dtstamp = now.strftime('%Y%m%dT%H%M%SZ')
#
#     for show in qs:
#         uid = f'{show.pk}@hella-reptilian-live'
#
#         if show.as_utc:
#             start_dt = show.as_utc
#             dtstart = start_dt.strftime('%Y%m%dT%H%M%SZ')
#         else:
#             if show.date:
#                 dtstart = show.date.strftime('%Y%m%d')
#             else:
#                 continue
#
#         title = show.title
#         venue_name = show.venue.name if show.venue_id else ''
#         location_parts = [venue_name, show.timezone]
#         location = ', '.join(p for p in location_parts if p)
#
#         lines.extend([
#             'BEGIN:VEVENT',
#             f'UID:{uid}',
#             f'DTSTAMP:{dtstamp}',
#             f'DTSTART:{dtstart}',
#             f'SUMMARY:{title}',
#             f'LOCATION:{location}',
#             'END:VEVENT',
#         ])
#
#     lines.append('END:VCALENDAR')
#
#     ical_content = '\r\n'.join(lines) + '\r\n'
#     response = HttpResponse(ical_content, content_type='text/calendar; charset=utf-8')
#     response['Content-Disposition'] = 'attachment; filename=\"live-shows.ics\"'
#     return response
#
#
#
#
#
# # -------------------------------------------------------------------
# # HTMX: /live/partial/past?page=n
# # -------------------------------------------------------------------
#
# def live_past_partial(request):
#     qs = Show.objects.past()
#     page_obj = _paginate(request, qs, per_page=10)
#
#     context = {
#         "page_obj": page_obj,
#         "shows": page_obj.object_list,
#     }
#     return render(request, 'hr_live/partials/past_list.html', context)
#
#
# # -------------------------------------------------------------------
# # Detail: /live/<slug>/ — show detail
# # -------------------------------------------------------------------
#
# def live_detail(request, slug):
#     show = get_object_or_404(Show, slug=slug, status="published")
#
#     context = {
#         "show": show,
#     }
#     return render(request, "hr_live/detail.html", context)
#
#
# # -------------------------------------------------------------------
# # HTMX: /live/partial/<slug>/card
# # -------------------------------------------------------------------
#
# def live_detail_card_partial(request, slug):
#     show = get_object_or_404(Show, slug=slug, status="published")
#
#     context = {
#         "show": show,
#     }
#     return render(request, "hr_live/partials/show_card.html", context)
#
#
# # -------------------------------------------------------------------
# # JSON: /api/live/shows/<slug>
# # -------------------------------------------------------------------
#
# def api_live_show_detail(request, slug):
#     show = get_object_or_404(Show, slug=slug, status="published")
#     data = _serialize_show(show)
#     return JsonResponse(data, status=200)
