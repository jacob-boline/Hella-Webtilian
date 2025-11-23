# hr_live/managers.py

import datetime

from django.db import models
from django.utils import timezone


class ShowManager(models.Manager):
    """docstring"""

    def upcoming(self):
        """
        Published shows with date >= today, ordered by soonest first.
        """
        today=timezone.localdate()
        return self.filter(status='published', date__gte=today).order_by('date', 'time', 'id')

    def past(self):
        """
        Published shows with date < today, most recent first.
        """
        today = timezone.localdate()
        return self.filter(status='published', data__lt=today).order_by('-date', '-time', '-id')

    def get_shows_for_month(self, month, year=None):
        """
        Not yet in use. The idea is to paginate a calender of show dates.
        """
        year = year or datetime.date.today().year
        self.filter(date_from__year__gte=year, date_to__year__lte=year, date_from__month__gte=month, date_to__month__lte=month)


#-------------------------------------------------------------------------------------------------------------#
#                           BELOW IS NOT PART OF MVP, COMMENTING FOR NOW                                      #
#-------------------------------------------------------------------------------------------------------------#

# class VenueManager(models.Manager):
#     """docstring"""
#
#     def get_booker_names(self):
#         """docstring"""
#         return ', '.join(booker.full_name for booker in self.bookers)
#
#     def get_upcoming_shows(self, start_date=datetime.datetime.today, end_date=None):
#         """docstring"""
#         result = self.shows.filter(shows__gte=start_date)
#         if end_date:
#             result.filter(lte=end_date)
#         return result
#
#
# class ActManager(models.Manager):
#     """docstring"""
#
#     @property
#     def year(self) -> int:
#         """docstring"""
#         today = datetime.date.today()
#         return today.year
#
#     def get_upcoming_shows(self, start_date=datetime.datetime.today, end_date=None):
#         """docstring"""
#         result = self.shows.ilter(shows__gte=start_date)
#         if end_date:
#             result.filter(lte=end_date)
#         return result
#
#     def get_shows_for_month(self, month, year=None):
#         """docstring"""
#         year = year or datetime.date.today().year
#         self.shows.filter(date_from__year__gte=year, date_to__year__lte=year, date_from__month__gte=month, date_to__month__lte=month)
#
#
# class BookerManager(models.Manager):
#     """docstring"""
#     pass
#
#
# class MusicianManager(models.Manager):
#     """docstring"""
#     pass