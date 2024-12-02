import datetime
# from datetime import datetime
from django.db import models
from datetime import datetime
# from django.db.models import Q


class AddressManager(models.Manager):
    pass


class ActManager(models.Manager):

    def get_upcoming_shows(self, start_date=datetime.today, end_date=None):
        result = self.shows.ilter(shows__gte=start_date)
        if end_date:
            result.filter(lte=end_date)
        return result

    def get_shows_for_month(self, month, year=None):
        year = year or datetime.date.today().year
        self.shows.filter(date_from__year__gte=year, date_to__year__lte=year, date_from__month__gte=month, date_to__month__lte=month)


class BookerManager(models.Manager):
    pass


class MusicianManager(models.Manager):
    pass


class ShowManager(models.Manager):

    def upcoming(self):
        shows = self.exclude(date__date__isnull=True).filter(date__date_gte=datetime.today)
        return shows

    def get_shows_for_month(self, month, year=None):
        year = year or datetime.date.today().year
        self.filter(date_from__year__gte=year, date_to__year__lte=year, date_from__month__gte=month,      date_to__month__lte=month)


class VenueManager(models.Manager):

    def get_booker_names(self):
        return ', '.join(booker.full_name for booker in self.bookers)

    def get_upcoming_shows(self, start_date=datetime.today, end_date=None):
        result = self.shows.filter(shows__gte=start_date)
        if end_date:
            result.filter(lte=end_date)
        return result
