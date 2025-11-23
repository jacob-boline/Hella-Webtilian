# hr_common/manager.py

from django.db import models


class AddressManager(models.Manager):
    pass

    def __str__(self):
        return 'AddressManager'

    def __init__(self):
        super().__init__()
        self.address = models.Manager()
