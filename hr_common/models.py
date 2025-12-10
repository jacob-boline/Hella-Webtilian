# hr_common/models.py

import urllib.parse
from django.db import models
from hr_common.managers import AddressManager


class Address(models.Model):
    street_address = models.CharField(max_length=255, blank=False, null=False, verbose_name='Address')
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
