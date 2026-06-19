# hr_live/models.py

import datetime
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db import models
from django.db.models import Q, QuerySet
from phonenumber_field.modelfields import PhoneNumberField
from phonenumber_field.phonenumber import PhoneNumber

from hr_common.db.slug import sync_slug_from_source
from hr_common.models import Address
from hr_live.managers import BookerManager, MusicianManager, ShowManager


def fmt(obj):
    if obj is None:
        return "N/A"
    if isinstance(obj, str):
        return obj.strip() or "N/A"
    return str(obj)


class Individual(models.Model):
    first_name = models.CharField(max_length=50, verbose_name="First Name")
    last_name = models.CharField(max_length=50, blank=True, verbose_name="Last Name")
    note = models.TextField(max_length=255, blank=True, verbose_name="Note")
    email = models.EmailField(blank=True, verbose_name="Email")
    phone_number = PhoneNumberField(blank=True, verbose_name="Phone")

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(fields=["email"], condition=~Q(email=""), name="uniq_nonblank_individual_email"),
            models.UniqueConstraint(fields=["phone_number"], condition=~Q(phone_number=""), name="uniq_nonblank_individual_phone_number")
        ]

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name or ""}'.strip()

    @property
    def formatted_phone(self) -> str:
        phone: PhoneNumber = self.phone_number
        return phone.as_national if phone else "N/A"


class Venue(models.Model):
    address = models.ForeignKey(Address, related_name="venues", null=True, verbose_name="Address", on_delete=models.PROTECT)  # not a one-to-one field for the case of a venue being renamed/sold
    bookers = models.ManyToManyField("Booker", related_name="venues", verbose_name="Bookers")
    note = models.TextField(max_length=5000, blank=True, verbose_name="Note")
    name = models.CharField(max_length=100, unique=True, verbose_name="Name")
    slug = models.SlugField(max_length=140, blank=True, unique=True)
    website = models.URLField(max_length=250, blank=True)
    email = models.EmailField(blank=True, max_length=254, verbose_name="Email")
    phone_number = PhoneNumberField(blank=True, verbose_name="Phone")

    class Meta:
        verbose_name_plural = "venues"
        ordering = ["name"]
        indexes = [models.Index(fields=["name"])]
        constraints = [
            models.UniqueConstraint(fields=["website"], condition=~Q(website=""), name="uniq_nonblank_venue_website"),
            models.UniqueConstraint(fields=["email"], condition=~Q(email=""), name="uniq_nonblank_venue_email"),
            models.UniqueConstraint(fields=["phone_number"], condition=~Q(phone_number=""), name="uniq_nonblank_venue_phone_number")
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        sync_slug_from_source(self, self.name, max_length=140)
        super().save(*args, **kwargs)

    @property
    def formatted_phone(self) -> str:
        phone: PhoneNumber = self.phone_number
        return phone.as_national if phone else "N/A"

    def get_fields(self) -> dict:
        return {
            "Venue": self.name,
            "Address": fmt(self.address),
            "Website": fmt(self.website),
            "Phone Number": self.formatted_phone,
            "Email": fmt(self.email),
            "Bookers": fmt(", ".join(booker.full_name for booker in self.bookers.all())),
            "IS_VENUE": "IS_VENUE"
        }

    @staticmethod
    def get_model():
        return Venue

    @staticmethod
    def model_name() -> str:
        return "Venues"

    @property
    def upcoming_shows(self) -> QuerySet:
        return Show.objects.upcoming().with_lineup_names()

    def add_booker(self, booker: "Booker") -> bool:
        if not isinstance(booker, Booker):
            return False
        added = not self.bookers.filter(pk=booker.pk).exists()
        if added:
            self.bookers.add(booker)
        return added

    def remove_booker(self, booker: "Booker") -> bool:
        if not isinstance(booker, Booker):
            return False
        removed = self.bookers.filter(pk=booker.pk).exists()
        if removed:
            self.bookers.remove(booker)
        return removed

    def get_booker_names(self):
        return ", ".join(booker.full_name for booker in self.bookers.all())


class Booker(Individual):
    objects = BookerManager()

    class Meta:
        verbose_name_plural = "bookers"
        ordering = ["first_name", "last_name", "phone_number", "email"]

    @staticmethod
    def get_model():
        return Booker

    @staticmethod
    def model_name():
        return "Bookers"

    def get_fields(self):
        return {"First Name": self.first_name, "Last Name": fmt(self.last_name), "Phone Number": self.formatted_phone, "Email": fmt(self.email), "IS_BOOKER": "IS_BOOKER"}

    def add_venue(self, venue: Venue) -> bool:
        if not isinstance(venue, Venue):
            return False
        added = not self.venues.filter(pk=venue.pk).exists()
        if added:
            self.venues.add(venue)
        return added

    def remove_venue(self, venue: Venue) -> bool:
        if not isinstance(venue, Venue):
            return False
        removed = self.venues.filter(pk=venue.pk).exists()
        if removed:
            self.venues.remove(venue)
        return removed

    @property
    def upcoming_shows(self) -> QuerySet:
        return Show.objects.upcoming()


class Musician(Individual):
    objects = MusicianManager()

    class Meta:
        verbose_name_plural = "musicians"

    @staticmethod
    def get_model():
        return Musician

    @staticmethod
    def get_name():
        return "Musicians"


class Act(models.Model):
    members  = models.ManyToManyField(Musician,  related_name="projects", verbose_name="Members")
    contacts = models.ManyToManyField(Musician,  related_name="contacts", verbose_name="Contacts")
    name     = models.CharField(max_length=255, unique=True)
    website  = models.URLField( max_length=255,  blank=True)
    note     = models.TextField(max_length=5000, blank=True, verbose_name="Note", default="")

    class Meta:
        verbose_name_plural = "acts"
        constraints = [
            models.UniqueConstraint(fields=["website"], condition=~Q(website=""), name="uniq_nonblank_act_website")
        ]

    def __str__(self):
        return self.name

    @staticmethod
    def get_model():
        return Act

    @staticmethod
    def model_name():
        return "Acts"

    def get_fields(self):
        members_qs = self.members.all()
        contacts_qs = self.contacts.all()

        return {
            "Act": self.name,
            "Website": fmt(self.website),
            "Members": fmt(", ".join(m.full_name for m in members_qs)),
            "Contacts": fmt(". ".join(c.full_name for c in contacts_qs)),
            "IS_ACT": "IS_ACT"
        }

    @property
    def upcoming_shows(self) -> QuerySet:
        return Show.objects.upcoming().card_ready()

    @property
    def all_shows(self) -> QuerySet:
        return self.shows.all()

    @property
    def past_shows(self) -> QuerySet:
        return Show.objects.past()


def show_image_storage(instance, filename):
    user_part = f"user_{instance.created_by.pk}" if instance.created_by_id else "user_unknown"
    return f"media/shows/{user_part}/{filename}"


class Show(models.Model):
    STATUS_CHOICES = [("draft", "Draft"), ("published", "Published")]

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, null=True, related_name="created")
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, null=True, related_name="updated")
    venue = models.ForeignKey(Venue, related_name="shows", verbose_name="Venue", on_delete=models.PROTECT)
    booker = models.ForeignKey(Booker, related_name="shows", verbose_name="Booker", on_delete=models.PROTECT, null=True)
    lineup = models.ManyToManyField(Act, related_name="shows", verbose_name="Lineup")
    date = models.DateField(null=True, blank=True, default=None, verbose_name="Date")
    time = models.TimeField(null=True, blank=True, default=None, verbose_name="Time")
    image = models.ImageField(upload_to=show_image_storage, max_length=100, null=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True, help_text="URL identifier auto-generated from date and venue.")
    status = models.CharField(max_length=10, default="draft", choices=STATUS_CHOICES)
    timezone = models.CharField(max_length=50, default="America/Chicago", verbose_name="Timezone")
    # to add a list of timezones add the following: choices=[(tz, tz) for tz in zoneinfo.available_timezones()],

    objects = ShowManager()

    class Meta:
        verbose_name_plural = "shows"
        ordering = ["date"]

    def __str__(self) -> str:
        date_str = self._formatted_date_short()
        time_str = self._formatted_time_short()
        venue_str = self.venue.name if self.venue_id else "Venue TBD"
        return f"{date_str} -- {venue_str} -- {time_str}"

    def save(self, *args, **kwargs):
        if self.date:
            sync_slug_from_source(self, self.date.isoformat(), max_length=140)
        super().save(*args, **kwargs)

    # helpers
    def _formatted_date_short(self) -> str:
        if not self.date:
            return "Date TBD"
        return self.date.strftime("%b %d %Y")

    def _formatted_time_short(self) -> str:
        if not self.time:
            return "Time TBD"
        return self.time.strftime("%I:%M %p").lstrip("0")

    def _formatted_date_long(self) -> str:
        if not self.date:
            return "Date TBD"
        return self.date.strftime("%A, %B %d, %Y")

    @staticmethod
    def get_model():
        return Show

    @staticmethod
    def model_name():
        return "Shows"

    def get_fields(self):
        return {
            "Date": fmt(self.date),
            "Time": fmt(self.time),
            "Venue": fmt(self.venue),
            "Booker": fmt(self.booker),
            "Lineup": fmt(", ".join(act.name for act in self.lineup.all())),
            "IS_SHOW": "IS_SHOW"
        }

    @property
    def title(self) -> str:
        return f"{self._formatted_date_short()} @ {self.venue.name if self.venue_id else 'Venue TBD'}"

    @property
    def subtitle(self) -> str:
        return f"Music @ {self._formatted_time_short()}"

    @property
    def readable_lineup(self) -> str:
        return " -- ".join(act.name for act in self.lineup.all()) or "Lineup TBD"

    @property
    def readable_details(self) -> str:
        date_str = self._formatted_date_long()
        venue_str = self.venue.name if self.venue_id else "Venue TBD"
        time_str = self._formatted_time_short()
        return f"{date_str} -- {venue_str} -- {time_str}"

    @property
    def naive_datetime(self):
        if not self.date or not self.time:
            return None
        return datetime.datetime.combine(self.date, self.time)

    @property
    def local_datetime(self):
        if not self.date or not self.time:
            return None
        return datetime.datetime.combine(self.date, self.time, tzinfo=ZoneInfo(self.timezone))

    @property
    def as_utc(self):
        dt = self.local_datetime
        return dt.astimezone(ZoneInfo("UTC")) if dt else None


class VenueBookerDay(models.Model):
    DAY_CHOICES = [("MON", "Monday"),("TUE", "Tuesday"),("WED", "Wednesday"),("THU", "Thursday"),("FRI", "Friday"),("SAT", "Saturday"),("SUN", "Sunday")]
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE)
    booker = models.ForeignKey(Booker, on_delete=models.CASCADE, null=True)
    day = models.CharField(max_length=3, choices=DAY_CHOICES, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["venue", "day"], name="uniq_venue_booker_day")
        ]
