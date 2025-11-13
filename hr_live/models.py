import datetime
import urllib.parse
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator, URLValidator
from django.db import models
from django.db.models import QuerySet, Prefetch
from phonenumber_field.modelfields import PhoneNumberField
from phonenumber_field.phonenumber import PhoneNumber
from django.conf import settings
from django.utils import timezone
from hr_live.managers import AddressManager, ActManager, BookerManager, MusicianManager, ShowManager, VenueManager
from zoneinfo import ZoneInfo


def fmt(obj):
    if obj is None:
        return "N/A"
    if isinstance(obj, str):
        return obj.strip() or "N/A"
    return str(obj)


class Address(models.Model):
    street_address = models.CharField(max_length=255, blank=False, null=False, unique=True, verbose_name="Address")
    city = models.CharField(max_length=255, blank=False, null=False, verbose_name="City")
    subdivision = models.CharField(max_length=255, blank=False, null=False, verbose_name="State/Province")
    postal_code = models.CharField(max_length=25, blank=False, null=True, verbose_name="Zip")
    country = models.CharField(max_length=255, blank=False, null=True, verbose_name="Country")

    objects = AddressManager()

    class Meta:
        verbose_name_plural = 'Addresses'

    def __str__(self):
        return f"{self.street_address}, {self.city}, {self.subdivision} {self.country}"

    @staticmethod
    def get_model():
        return Address

    @staticmethod
    def model_name():
        return 'Addresses'

    def get_fields(self):
        return {
            'Address':        self.street_address,
            'City':           self.city,
            'State/Province': self.subdivision,
            'Zip':            self.postal_code,
            'Country':        self.country,
            'IS_ADDRESS':     'IS_ADDRESS'
        }

    @property
    def directions(self) -> str:
        destination = urllib.parse.quote_plus(f'{self.street_address} {self.city}, {self.subdivision}')
        directions_url = f'https://www.google.com/maps/dir/?api=1&destination={destination}&basemap=satellite'
        return directions_url


class Individual(models.Model):
    first_name = models.CharField(max_length=50, blank=False, null=False, verbose_name="First Name")
    last_name = models.CharField(max_length=50, blank=False, null=True, verbose_name="Last Name")
    phone_number = PhoneNumberField(blank=True, null=True, unique=True, verbose_name="Phone")
    email = models.EmailField(blank=True, null=True, unique=True, validators=[EmailValidator()], verbose_name="Email")
    note = models.TextField(max_length=255, blank=True, null=True, verbose_name="Note")

    class Meta:
        abstract = True

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name or ""}'.strip()

    @property
    def formatted_phone(self) -> str:
        phone: PhoneNumber = self.phone_number
        return phone.as_national if phone else "N/A"


class Day(models.Model):
    DAY_CHOICES = (
        ('MON', 'Monday'),
        ('TUE', 'Tuesday'),
        ('WED', 'Wednesday'),
        ('THU', 'Thursday'),
        ('FRI', 'Friday'),
        ('SAT', 'Saturday'),
        ('SUN', 'Sunday')
    )

    name = models.CharField(choices=DAY_CHOICES, max_length=10, blank=True, null=True, verbose_name="Day of the Week")


class Venue(models.Model):
    name = models.CharField(max_length=100, blank=False, null=False, unique=True, verbose_name="Name")
    website = models.URLField(max_length=250, blank=False, null=True, unique=True, validators=[URLValidator()])
    phone_number = PhoneNumberField(blank=True, null=True, unique=True, verbose_name="Phone")
    email = models.EmailField(blank=True, null=True, unique=True, verbose_name="Email", validators=[EmailValidator()])
    note = models.TextField(max_length=5000, blank=True, null=True, verbose_name="Note")
    bookers = models.ManyToManyField("Booker", related_name="venues", verbose_name="Bookers")
    address = models.ForeignKey(Address, related_name="venue", verbose_name="Address", on_delete=models.PROTECT, null=True)

    objects = VenueManager()

    class Meta:
        verbose_name_plural = "venues"
        ordering = ["name"]
        indexes = [models.Index(fields=["name"])]

    def __str__(self):
        return self.name

    @property
    def formatted_phone(self) -> str:
        phone: PhoneNumber = self.phone_number
        return phone.as_national if phone else "N/A"

    def get_fields(self) -> dict:
        return {
            'Venue':        self.name,
            'Address':      fmt(self.address),
            'Website':      fmt(self.website),
            'Phone Number': self.formatted_phone,
            'Email':        fmt(self.email),
            'Bookers':      fmt(", ".join(booker.full_name for booker in self.bookers.all())),
            'IS_VENUE':     'IS_VENUE'
        }

    @staticmethod
    def get_model():
        return Venue

    @staticmethod
    def model_name() -> str:
        return 'Venues'

    @property
    def upcoming_shows(self) -> QuerySet:
        today = timezone.now().date()
        return self.shows.filter(date__gte=today).prefetch_related("lineup")

    @staticmethod
    def validate_url(url: str) -> bool:
        url_validator = URLValidator()
        try:
            url_validator(url)
            return True
        except ValidationError:
            return False

    def add_booker(self, booker: "Booker") -> bool:
        if not isinstance(booker, Booker):
            return False

        added = not self.bookers.filter(pk=booker.pk).exists()
        if added:
            self.bookers.add(booker)
            self.save()

        return added

    def remove_booker(self, booker: "Booker") -> bool:
        if not isinstance(booker, Booker):
            return False

        removed = self.bookers.filter(pk=booker.pk).exists()
        if removed:
            self.bookers.remove(booker)
            self.save()

        return removed


class Booker(Individual):
    objects = BookerManager()

    class Meta:
        verbose_name_plural = "bookers"
        ordering = ['first_name', 'last_name', 'phone_number', 'email', 'nickname']

    @staticmethod
    def get_model():
        return Booker

    @staticmethod
    def model_name():
        return 'Bookers'

    def get_fields(self):
        return {
            'First Name':   self.first_name,
            'Last Name':    fmt(self.last_name),
            'Phone Number': self.formatted_phone,
            'Email':        fmt(self.email),
            'IS_BOOKER':    'IS_BOOKER'
        }

    def add_venue(self, venue: Venue) -> bool:
        if not isinstance(venue, Venue):
            return False

        added = not self.venues.filter(pk=venue.pk).exists()
        if added:
            self.venues.add(venue)
            self.save()

        return added

    def remove_venue(self, venue: Venue) -> bool:
        if not isinstance(venue, Venue):
            return False

        removed = self.venues.filter(pk=venue.pk).exists()
        if removed:
            self.venues.remove(venue)
            self.save()

        return removed

    @property
    def upcoming_shows(self) -> QuerySet:
        today = timezone.now().date()
        return self.shows.filter(date__gte=today)


class Musician(Individual):
    objects = MusicianManager()

    class Meta:
        verbose_name_plural = "musicians"

    @staticmethod
    def get_model():
        return Musician

    @staticmethod
    def get_name():
        return 'Musicians'


class Act(models.Model):
    name = models.CharField(max_length=255, blank=False, null=False, unique=True)
    website = models.URLField(max_length=255, blank=False, null=True, unique=True, validators=[URLValidator()])
    members = models.ManyToManyField(Musician, related_name="projects", verbose_name="Members")
    contacts = models.ManyToManyField(Musician, related_name="contacts", verbose_name="Contacts")
    note = models.TextField(max_length=5000, blank=True, null=True, verbose_name="Note")

    objects = ActManager()

    class Meta:
        verbose_name_plural = "acts"

    def __str__(self):
        return self.name

    @staticmethod
    def get_model():
        return Act

    @staticmethod
    def model_name():
        return 'Acts'

    def get_fields(self):
        members_qs = self.members.all()
        contacts_qs = self.contacts.all()

        return {
            "Act":      self.name,
            "Website":  fmt(self.website),
            "Members":  fmt(", ".join(m.full_name for m in members_qs)),
            "Contacts": fmt(". ".join(c.full_name for c in contacts_qs)),
            "IS_ACT":   "IS_ACT",
        }

    @property
    def upcoming_shows(self) -> QuerySet:
        today = timezone.now().date()
        return (
            self.shows
            .filter(date__gte=today)
            .select_related("venue")
            .prefetch_related(
                Prefetch(
                    "lineup",
                    queryset=Act.objects.only("id", "name")
                )
            )
            .only('id', 'date', 'time', 'venue')
        )

    @property
    def all_shows(self) -> QuerySet:
        return self.shows.all()

    @property
    def past_shows(self) -> QuerySet:
        today = timezone.now().date()
        return self.shows.filter(date__lt=today)


def show_image_storage(instance, filename):
    user_part = f"user_{instance.created_by.pk}" if instance.created_by_id else "user_unknown"
    return f"{user_part}/{filename}"


class Show(models.Model):
    date = models.DateField(null=True, blank=False, default=None, verbose_name="Date")
    time = models.TimeField(null=True, blank=False, default=None, verbose_name="Time")
    # to add a list of timezones add the following: choices=[(tz, tz) for tz in zoneinfo.available_timezones()],
    timezone = models.CharField(max_length=50, default="America/Chicago", verbose_name="Timezone")
    venue = models.ForeignKey(Venue, related_name="shows", verbose_name="Venue", on_delete=models.PROTECT)
    booker = models.ForeignKey(Booker, related_name="shows", verbose_name="Booker", on_delete=models.PROTECT, null=True)
    lineup = models.ManyToManyField(Act, related_name="shows", verbose_name="Lineup")
    image = models.ImageField(upload_to=show_image_storage, max_length=100, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, null=True, related_name="created")
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, null=True, related_name="updated")
    # doors = models.DateTimeField(null=True, blank=False, default=None, verbose_name="Show Time")
    # note = models.TextField(max_length=5000, blank=True, null=True, verbose_name="Note")

    objects = ShowManager()

    class Meta:
        verbose_name_plural = "shows"
        ordering = ["date"]

    def __str__(self) -> str:
        date_str = self._formatted_date_short()
        venue_str = self.venue.name if self.venue_id else "Venue TBD"
        time_str = self._formatted_time_short()

        return f"{date_str} -- {venue_str} -- {time_str}"

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
        return 'Shows'

    def get_fields(self):
        return {
            'Date':    fmt(self.date),
            'Time':    fmt(self.time),
            'Venue':   fmt(self.venue),
            'Booker':  fmt(self.booker),
            'Lineup':  fmt(", ".join(act.name for act in self.lineup.all())),
            'IS_SHOW': 'IS_SHOW'
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
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, unique=False, blank=False, null=False)
    booker = models.ForeignKey(Booker, on_delete=models.CASCADE, unique=False, blank=False, null=True)
    day = models.ForeignKey(Day, on_delete=models.PROTECT, unique=False, blank=False, null=True)

    class Meta:
        unique_together = ('venue', 'day')
