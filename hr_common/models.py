# hr_common/models.py

import hashlib
import re
import urllib.parse
from django.db import models
from hr_common.managers import AddressManager

_whitespace = re.compile(r"\s+")


def _norm(s: str | None) -> str:
    if not s:
        return ""
    return _whitespace.sub(" ", s.strip()).casefold()


def _fp(*parts: str) -> str:
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


class BuildingType(models.TextChoices):
    SINGLE_FAMILY = "single_family", "Single family home"
    APARTMENT = "apartment", "Apartment / Condo"
    BUSINESS = "business", "Business"
    PO_BOX = "po_box", "P.O. Box"
    OTHER = "other", "Other"


class Address(models.Model):
    fingerprint = models.CharField(max_length=64, unique=True, db_index=True, editable=False)

    street_address = models.CharField(max_length=255, blank=False, null=False, verbose_name='Address')
    street_address_line2 = models.CharField(max_length=255, blank=True, null=True, verbose_name="Address Line 2")
    building_type = models.CharField(max_length=20, choices=BuildingType.choices, default=BuildingType.SINGLE_FAMILY)
    unit = models.CharField(max_length=50, blank=True, null=True, verbose_name='Apt/Office/Unit')
    city = models.CharField(max_length=255, blank=False, null=False, verbose_name='City')
    subdivision = models.CharField(max_length=100, blank=False, null=False, verbose_name='State/Province')
    postal_code = models.CharField(max_length=25, blank=False, null=False, verbose_name='Zip')
    country = models.CharField(max_length=255, blank=False, null=False, verbose_name='Country')

    objects = AddressManager()

    class Meta:
        verbose_name_plural = 'Addresses'

    @classmethod
    def compute_fingerprint_from_components(
            cls,
            *,
            street_address: str,
            street_address_line2: str | None,
            building_type: str,
            unit: str | None,
            city: str,
            subdivision: str,
            postal_code: str,
            country: str,
    ) -> str:
        raw = "|".join([
            _norm(street_address),
            _norm(street_address_line2),
            _norm(building_type),
            _norm(unit),
            _norm(city),
            _norm(subdivision),
            _norm(postal_code),
            _norm(country),
        ])
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def save(self, *args, **kwargs):
        # Always keep fingerprint consistent with content.
        self.fingerprint = self.compute_fingerprint_from_components(
            street_address=self.street_address,
            street_address_line2=self.street_address_line2,
            building_type=self.building_type,
            unit=self.unit,
            city=self.city,
            subdivision=self.subdivision,
            postal_code=self.postal_code,
            country=self.country,
        )
        super().save(*args, **kwargs)

    def __str__(self):
        # TODO omit the country when it is the US
        return f"{self.street_address} {self.city}, {self.subdivision} {self.postal_code} {self.country}"

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

    @property
    def formatted(self):
        """
        Return a plain-text, multi-line shipping address.
        """
        lines = []

        if self.street_address:
            lines.append(self.street_address)

        if self.street_address_line2:
            lines.append(self.street_address_line2)

        if self.unit:
            lines.append(f"Unit {self.unit}")

        city_line = ", ".join(
            filter(None, [self.city, self.subdivision])
        )
        if self.postal_code:
            city_line = f"{city_line} {self.postal_code}"

        if city_line.strip():
            lines.append(city_line)

        return "\n".join(lines)
