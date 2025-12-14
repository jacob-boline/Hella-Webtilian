# hr_common/models.py

import urllib.parse
from django.db import models
from hr_common.managers import AddressManager


class Address(models.Model):
    street_address = models.CharField(max_length=255, blank=False, null=False, verbose_name='Address')
    street_address_line2 = models.CharField(max_length=255, blank=True, null=True, verbose_name="Address Line 2")
    unit = models.CharField(max_length=50, blank=True, null=True, verbose_name='Apt/Office/Unit')
    city = models.CharField(max_length=255, blank=False, null=False, verbose_name='City')
    subdivision = models.CharField(max_length=100, blank=False, null=False, verbose_name='State/Province')
    postal_code = models.CharField(max_length=25, blank=False, null=False, verbose_name='Zip')
    country = models.CharField(max_length=255, blank=False, null=False, verbose_name='Country')

    objects = AddressManager()

    class Meta:
        verbose_name_plural = 'Addresses'

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

