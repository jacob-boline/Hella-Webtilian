# hr_live/managers.py

from __future__ import annotations

import datetime

from django.db import models
from django.db.models import Prefetch
from django.utils import timezone


# noinspection PyTypeChecker
class ShowQuerySet(models.QuerySet):
    def upcoming(self) -> "ShowQuerySet":
        return self.filter(date__gte=timezone.localdate())

    def past(self) -> "ShowQuerySet":
        return self.filter(date__lt=timezone.localdate())

    def get_shows_for_month(self, month, year=None) -> "ShowQuerySet":
        """Not yet in use. The idea is to paginate a calender of show dates."""
        year = year or datetime.date.today().year
        return self.filter(date_from__year__gte=year, date_to__year__lte=year, date_from__month__gte=month, date_to__month__lte=month)


    def with_venue(self) -> "ShowQuerySet":
        return self.select_related("venue")

    def with_lineup_names(self) -> "ShowQuerySet":
        from hr_live.models import Act
        return self.prefetch_related(
            Prefetch("lineup", queryset=Act.objects.only("id", "name"))
        )

    def card_ready(self) -> "ShowQuerySet":
        return self.with_venue().with_lineup_names().only("id", "date", "time", "venue")

    def for_schedule_cards(self):
        from hr_live.models import Act
        return self.select_related("venue").prefetch_related(
            Prefetch("lineup", queryset=Act.objects.only("id", "name"))
        )


class ShowManager(models.Manager.from_queryset(ShowQuerySet)):
    pass


class BookerManager(models.Manager):
    pass


class MusicianManager(models.Manager):
    pass
