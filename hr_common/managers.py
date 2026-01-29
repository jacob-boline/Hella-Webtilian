# hr_common/managers.py

from django.db import IntegrityError, models, transaction


class AddressManager(models.Manager):

    def __str__(self):
        return "AddressManager"

    def __init__(self):
        super().__init__()
        self.address = models.Manager()

    def get_or_create_by_components(self, **components):
        from hr_common.models import Address  # avoid circular import at module load

        fingerprint = Address.compute_fingerprint_from_components(**components)

        try:
            with transaction.atomic():
                obj = self.create(fingerprint=fingerprint, **components)
                return obj, True
        except IntegrityError:
            return self.get(fingerprint=fingerprint), False
