import urllib.parse
# from datetime import datetime
# from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator, URLValidator
from django.db import models
# from django.db.models import QuerySet
from phonenumber_field.modelfields import PhoneNumberField
from django.conf import settings
from hr_live.managers import\
    AddressManager, ActManager, BookerManager, MusicianManager, ShowManager, VenueManager


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
            'Address': self.street_address,
            'City': self.city,
            'State/Province': self.subdivision,
            'Zip': self.postal_code,
            'Country': self.country,
            'IS_ADDRESS': 'IS_ADDRESS'
        }

    @property
    def directions(self) -> str:
        destination = urllib.parse.quote_plus(f'{self.street_address} {self.city}, {self.subdivision}')
        directions_url = f"https://www.google.com/maps/dir/?api=1&destination={destination}&basemap=satellite"
        return directions_url


class Individual(models.Model):
    first_name = models.CharField(max_length=50, blank=False, null=False, verbose_name="First Name")
    last_name = models.CharField(max_length=50, blank=False, null=True, verbose_name="Last Name")
    phone_number = PhoneNumberField(blank=True, null=True, verbose_name="Phone")
    email = models.EmailField(blank=True, null=True, validators=[EmailValidator, ], verbose_name="Email")
    # address = models.ForeignKey(Address, blank=False, null=True, verbose_name="Address", on_delete=models.PROTECT)
    note = models.TextField(max_length=255, blank=True, null=True, verbose_name="Note")

    class Meta:
        abstract = True

    def __str__(self):
        display_name = self.first_name
        if self.last_name:
            display_name += f' {self.last_name}'
        return display_name

    def full_name(self):
        return f'{self.first_name} {self.last_name if self.last_name else ""}'


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

    name = models.CharField(choices=DAY_CHOICES, max_length=10, blank=False, null=True, verbose_name="Day of the Week")


class Booker(Individual):
    first_name = models.CharField(max_length=50, blank=False, null=False, verbose_name="First Name")
    last_name = models.CharField(max_length=50, blank=False, null=True, verbose_name="Last Name")
    nickname = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nickname")
    phone_number = PhoneNumberField(blank=False, null=True, unique=True, verbose_name="Phone Number")
    email = models.EmailField(blank=False, null=True, unique=True, validators=[EmailValidator, ])

    objects = BookerManager()

    class Meta:
        verbose_name_plural = "bookers"
        ordering = ['first_name', 'last_name', 'phone_number', 'email', 'nickname']

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    @staticmethod
    def get_model():
        return Booker

    @staticmethod
    def model_name():
        return 'Bookers'

    def get_fields(self):
        return {
            'First Name': self.first_name,
            'Last Name': self.last_name if self.last_name else 'N/A',
            'Nickname': self.nickname if self.nickname else 'N/A',
            'Phone Number': self.phone_number if self.phone_number else 'N/A',
            'Email': self.email if self.email else 'N/A',
            'IS_BOOKER': 'IS_BOOKER'
        }

    # def add_venue(self, venue):
    #     self.venues.add

    # def add_venue(self, venue) -> bool:
    #     if isinstance(venue, Venue) and venue not in self.venues:
    #         self.venues.add(venue)
    #         self.save()
    #         return True
    #     return False
    #
    # def remove_venue(self, venue) -> bool:
    #     if venue in self.venues:
    #         venue.remove(self)
    #         self.save()
    #         return True
    #     return False

    # @property
    # def upcoming_shows(self) -> QuerySet
    #     # return self.shows.filter(date__gte=datetime.today())
    #     return Show.objects.filter(date__gte=datetime.today()).filter(booker=self)


class Venue(models.Model):
    name = models.CharField(max_length=100, blank=False, null=False, unique=True, verbose_name="Name")
    website = models.URLField(max_length=250, blank=False, null=True, unique=True, validators=[URLValidator, ])
    phone_number = PhoneNumberField(blank=False, null=True, unique=True, verbose_name="Phone")
    email = models.EmailField(blank=False, null=True, unique=True, validators=[EmailValidator, ], verbose_name="Email")
    bookers = models.ManyToManyField(Booker, related_name="venues", verbose_name="Bookers")
    address = models.ForeignKey(Address, related_name="venue", verbose_name="Address", on_delete=models.PROTECT, null=True)
    note = models.TextField(max_length=5000, blank=True, null=True, verbose_name="Note")

    objects = VenueManager()

    class Meta:
        verbose_name_plural = "venues"
        ordering = ["name"]
        indexes = [models.Index(fields=["name"])]

    def __str__(self):
        return self.name

    def get_fields(self):
        return {
            'Venue': self.name,
            'Address': self.address if self.address else 'N/A',
            'Website': self.website if self.website else 'N/A',
            'Phone Number': self.phone_number if self.phone_number else 'N/A',
            'Email': self.email if self.email else 'N/A',
            # 'Bookers': '. '.join(booker.full_name for booker in self.bookers if self.bookers)
            # 'Bookers': ', '.join([f'{booker.first_name} {booker.last_name}' for booker in self.bookers.all()]),
            'IS_VENUE': 'IS_VENUE'
        }

    @staticmethod
    def get_model():
        return Venue

    @staticmethod
    def model_name():
        return 'Venues'

    # @property
    # def upcoming_shows(self) -> QuerySet:
    #     return self.show_set.filter(date_gte=datetime.today())
    #

    @staticmethod
    def validate_url(url: str) -> bool:
        url_validator = URLValidator()
        try:
            url_validator(url)
            return True
        except ValidationError:
            return False

    # def add_booker(self, booker):
    #     self.bookers.add(booker)
    #     self.save()


class Musician(Individual):
    stage_name = models.CharField(max_length=50, blank=False, null=True)

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
    website = models.URLField(max_length=255, blank=False, null=True, unique=True, validators=[URLValidator, ])
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
        return {
            'Act': self.name,
            'Website': self.website if self.website else 'N/A',
            'Members': ', '.join([f'{member.first_name} {member.last_name}' for member in self.objects.members_set.all()]) if self.members else 'N/A',
            'Contacts': '. '.join([f'{contact.first_name} {contact.last_name}' for contact in self.objects.contacts_set.all()]) if self.contacts else 'N/A',
            'IS_ACT': 'IS_ACT'
        }

    # @property
    # def upcoming_shows(self) -> QuerySet:
    #     return Show.objects.filter(Artist=self, date__gte=datetime.today())\
    #         .prefetch_related(Show).only('lineup', 'date', 'time', 'venue')

    # @property
    # def all_shows(self) -> QuerySet:
    #     return Show.objects.filter(Artist=self)
    #
    # @property
    # def past_shows(self) -> QuerySet:
    #     return Show.objects.filter(Artist=self, date__lt=datetime.today())


def show_image_storage(instance, filename):
    # return f"user_{instance.created_by.pk}/{filename}"
    return f"{filename}"


class Show(models.Model):
    date = models.DateField(null=True, blank=False, default=None, verbose_name="Date")
    time = models.TimeField(null=True, blank=False, default=None, verbose_name="Time")
    # doors = models.DateTimeField(null=True, blank=False, default=None, verbose_name="Show Time")
    venue = models.ForeignKey(Venue, related_name="shows", verbose_name="Venue", on_delete=models.PROTECT)
    booker = models.ForeignKey(Booker, related_name="shows", verbose_name="Booker", on_delete=models.PROTECT, null=True)
    lineup = models.ManyToManyField(Act, related_name="shows", verbose_name="Lineup")
    # note = models.TextField(max_length=5000, blank=True, null=True, verbose_name="Note")
    image = models.ImageField(upload_to=show_image_storage, height_field=None, width_field=None, max_length=100, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, null=True, related_name="create")
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, null=True, related_name="update")

    objects = ShowManager()

    class Meta:
        verbose_name_plural = "shows"
        ordering = ["date"]

    # def __str__(self):
    #     return f"{datetime.date(self.doors).strftime('%m//%a')} -- {self.venue.name} -- {datetime.date(self.doors).strftime('%I:%M %p')}"
    #
    # def __str__(self):
    #     return f"{self.date.strftime('%m//%a')} -- {self.venue.name} -- {self.time.strftime('%I:%M %p')}"

    @staticmethod
    def get_model():
        return Show

    @staticmethod
    def model_name():
        return 'Shows'

    def get_fields(self):
        return {
            'Date': self.date if self.date else 'N/A',
            'Time': self.time if self.time else 'N/A',
            'Venue': self.venue if self.venue else 'N/A',
            'Booker': self.booker if self.booker else 'N/A',
            # 'Lineup': ', '.join([f'{artist.name}' for artist in self.lineup.all()]),
            'IS_SHOW': 'IS_SHOW'
        }

    @property
    def title(self):
        return f"{self.date} @ {self.venue.name}"

    @property
    def subtitle(self):
        return f"Music @ {self.time} @ need a show.price attribute on model"

    @property
    def readable_lineup(self):
        lineup = ''
        artists = [artist.name for artist in self.lineup.all()]
        for artist in artists:
            lineup += artist
            if artist != artists[-1]:
                lineup += ' -- '
        return lineup

    @property
    def readable_details(self):
        return f"{self.date if self.date else 'Date TBD'} -- {self.venue.name if self.venue else 'Venue TBD'} -- {self.time if self.time else 'Doors TBD'}"
        # return f"{self.date.strftime('%A %B %-d')} -- {self.venue.name} -- {self.time}"

    @property
    def details(self):
        return f"{self.readable_lineup}"


class VenueBookerDay(models.Model):
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, unique=False, blank=False, null=False)
    booker = models.ForeignKey(Booker, on_delete=models.CASCADE, unique=False, blank=False, null=True)
    day = models.ForeignKey(Day, on_delete=models.PROTECT, unique=False, blank=False, null=True)

    class Meta:
        unique_together = ('venue', 'day')
