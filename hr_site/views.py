from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import render, redirect
from datetime import datetime
from django.contrib import messages
from zoneinfo import ZoneInfo  # Python 3.9+


import json
from django.utils import timezone
from django.conf import settings
import os

from hr_live.managers import ShowManager
from hr_live.models import Show, Venue, Act, Booker


def index2(request):
    tinymce_key = os.getenv('TINYMCE_API_KEY')
    return render(request, 'hr_site/base.html', {'tinymce_api_key': tinymce_key})


def get_audio_stream_player(request):
    return render(request, "hr_site/audio_stream.html")


timezone_america = {
    'Adak': 'America/Adak',
    'Anchorage': 'America/Anchorage',
    'Boise': 'America/Boise',
    'Cambridge Bay': 'America/Cambridge Bay',
    'Chicago': 'America/Chicago',
    'Dawson': 'America/Dawson',
    'Dawson Creek': 'America/Dawson_Creek',
    'Denver': 'America/Denver',
    'Detroit': 'America/Detroit',
    'Edmonton': 'America/Edmonton',
    'Fort Nelson': 'America/Fort_Nelson',
    'Glace Bay': 'America/Glace_Bay',
    'Goose Bay': 'America/Goose_Bay',
    'Halifax': 'America/Halifax',
    'Indiana/Indianapolis': 'America/Indiana/Indianapolis',
    'Indiana/Knox': 'America/Indiana/Knox',
    'Indiana/Marengo': 'America/Indiana/Marengo',
    'Indiana/Petersburg': 'America/Indiana/Petersburg',
    'Indiana/Tell City': 'America/Indiana/Tell_City',
    'Indiana/Vevay': 'America/Indiana/Vevay',
    'Indiana/Vincennes': 'America/Indiana/Vincennes',
    'Indiana/Winamac': 'America/Indiana/Winamac',
    'Inuvik': 'America/Inuvik',
    'Iqaluit': 'America/Iqaluit',
    'Juneau': 'America/Juneau',
    'Kentucky/Louisville': 'America/Kentucky/Louisville',
    'Kentucky/Monticello': 'America/Kentucky/Monticello',
    'Los Angeles': 'America/Los_Angeles',
    'Menominee': 'America/Menominee',
    'Metlakatla': 'America/Metlakatla',
    'Moncton': 'America/Moncton',
    'New York': 'America/New_York',
    'Nipigon': 'America/Nipigon',
    'Nome': 'America/Nome',
    'North Dakota/Beulah': 'America/North_Dakota/Beulah',
    'North Dakota/Center': 'America/North_Dakota/Center',
    'North Dakota/New Salem': 'America/North_Dakota/New_Salem',
    'Panama': 'America/Panama',
    'Pangnirtung': 'America/Pangnirtung',
    'Phoenix': 'America/Phoenix',
    'Puerto Rico': 'America/Puerto_Rico',
    'Rainy River': 'America/Rainy_River',
    'Rankin Inlet': 'America/Rankin_Inlet',
    'Regina': 'America/Regina',
    'Resolute': 'America/Resolute',
    'Sitka': 'America/Sitka',
    'St. Johns': 'America/St_Johns',
    'Swift Current': 'America/Swift_Current',
    'Thunder Bay': 'America/Thunder_Bay',
    'Toronto': 'America/Toronto',
    'Vancouver': 'America/Vancouver',
    'Whitehorse': 'America/Whitehorse',
    'Winnipeg': 'America/Winnipeg',
    'Yakutat': 'America/Yakutat',
    'Yellowknife': 'America/Yellowknife'
}

timezone_atlantic = {
    'Azores': 'Atlantic/Azores',
    'Bermuda': 'Atlantic/Bermuda',
    'Canary': 'Atlantic/Canary',
    'Faroe': 'Atlantic/Faroe',
    'Madeira': 'Atlantic/Madeira',
    'Raykjavik': 'Atlantic/Raykjavik'
}

timezone_asia = {
    'Hong Kong': 'Asia/Hong_Kong',
    'Seoul': 'Asia/Seoul',
    'Taipei': 'Asia/Taipei',
    'Tokyo': 'Asia/Tokyo',
}

timezone_australia = {
    'Adelaide': 'Australia/Adelaide',
    'Brisbane': 'Australia/Brisbane',
    'Broken Hill': 'Australia/Broken_Hill',
    'Darwin': 'Australia/Darwin',
    'Eucia': 'Australian/Eucia',
    'Hobart': 'Australian/Hobart',
    'Lindeman': 'Australia/Lindeman',
    'Lord Howe': 'Australian/Lord_Howe',
    'Melbourne': 'Australia/Melbourne',
    'Perth': 'Australia/Perth',
    'Sydney': 'Australia/Sydney'
}

timezone_europe = {
    'Amsterdam': 'Europe/Amsterdam',
    'Andorra': 'Europe/Andorra',
    'Athens': 'Europe/Athens',
    'Belgrade': 'Europe/Belgrade',
    'Berlin': 'Europe/Berlin',
    'Brussels': 'Europe/Brussels',
    'Bucharest': 'Europe/Bucharest',
    'Budapest': 'Europe/Budapest',
    'Chisinau': 'Europe/Chisinau',
    'Copenhagen': 'Europe/Copenhagen',
    'Dublin': 'Europe/Dublin',
    'Gibraltar': 'Europe/Gibraltar',
    'Helsinki': 'Europe/Helsinki',
    'Istanbul': 'Europe/Istanbul',
    'Kiev': 'Europe/Kiev',
    'Lisbon': 'Europe/Lisbon',
    'London': 'Europe/London',
    'Luxembourg': 'Europe/Luxembourg',
    'Madrid': 'Europe/Madrid',
    'Malta': 'Europe/Malta',
    'Minsk': 'Europe/Minsk',
    'Monaco': 'Europe/Monaco',
    'Oslo': 'Europe/Oslo',
    'Paris': 'Europe/Paris',
    'Prague': 'Europe/Prague',
    'Riga': 'Europe/Riga',
    'Rome': 'Europe/Rome',
    'Simferopol': 'Europe/Simferopol',
    'Sofia': 'Europe/Sofia',
    'Stockholm': 'Europe/Stockholm',
    'Tallinn': 'Europe/Tallinn',
    'Tirane': 'Europe/Tirane',
    'Uzhgorod': 'Europe/Uzhgorod',
    'Vienna': 'Europe/Vienna',
    'Vilnius': 'Europe/Vilnius',
    'Warsaw': 'Europe/Warsaw',
    'Zaporozhye': 'Europe/Zaporozhye',
    'Zurich': 'Europe/Zurich'
}

timezone_us = {
    'Alaska': 'US/Alaska',
    'Aleutian': 'US/Aleutian',
    'Arizona': 'US/Arizona',
    'Central': 'US/Central',
    'Eastern': 'US/Eastern',
    'Hawaii': 'US/Hawaii',
    'Mountain': 'US/Mountain',
    'Pacific': 'US/Pacific'
}

timezone_pacific = {
    'Aukland': 'Pacific/Aukland',
    'Chatham': 'Pacific/Chatham',
    'Guam': 'Pacific/Guam',
    'Honolulu': 'Pacific/Honolulu',
    'Pago Pago': 'Pacific/Pago_Pago',
    'Wake': 'Pacific/Wake',
}

#
# def set_timezone(request):
#     if request.method == 'POST':
#         request.session['django_timezone'] = request.POST['timezone-select']
#         request.session.save()
#         response = HttpResponse(status=204)
#         trigger_dict = {
#             'timezoneChanged': None,
#             'showMessage': f'Timezone Updated to {request.session["django_timezone"]}',
#             'messageChanged': None
#         }
#         response.headers['HX-Trigger'] = json.dumps(trigger_dict)
#         return response
#     else:
#         reference_date = datetime(year=2024, day=5, hour=0, minute=0, second=0)
#         server_time = timezone.localtime(timezone.now())
#         if request.session.get('django-timezone', False):
#             old_tz = request.session['django_timezone']
#             request_tz = ZoneInfo(request.session['django_timezone'])
#             session_tz = timezone.activate(request_tz)
#             session_time = timezone.localtime(timezone.now())
#         else:
#             request.session['django_timeszone'] = settings.TIME_ZONE
#             request_tz = ZoneInfo(request.session['django_timezone'])
#             session_tz = timezone.activate(request_tz)
#             session_time = timezone.localtime(timezone.now())
#             request.session['django_timezone'] = settings.TIME_ZONE
#             request.session.save()
#         return render(request, 'hr_site/timezones.html', {'timezones': timezone_us})


def get_messsages(request):
    return render(request, 'hr_site/messages.html')


# def clear_messages(request):
#     return render(request, 'hr_site/messages_partial.html')


def comment_form(request):
    if request.method == 'GET':
        return
    return


def index(request):
    return render(request, "hr_site/index.html")


# def test2(request):
#     return render(request, "hr_site/test2.html")
#
#
# def burn_test(request):
#     return render(request, "hr_site/burn_test.html")
#
#
# def parallax_test(request):
#     return render(request, "hr_site/parallax_test.html")
#
#
# def pt2(request):
#     return render(request, "hr_site/pt2.html")


def pt3(request):
    shows = Show.objects.exclude(date__isnull=True).filter(date__gte=datetime.today())
    return render(request, "hr_site/pt3.html", {"upcoming": shows})


def pt4(request):
    return render(request, "hr_site/pt4.html")


def pt5(request):
    return render(request, "hr_site/pt5.html")


def pt6(request):
    return render(request, "hr_site/pt6.html")
