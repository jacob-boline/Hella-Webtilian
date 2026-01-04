# hr_core/db/fields.py

from django.db import models
from hr_core.utils.email import normalize_email


class NormalizedEmailField(models.EmailField):
    def pre_save(self, model_instance, add):
        val = getattr(model_instance, self.attname)
        val = normalize_email(val)
        setattr(model_instance, self.attname, val)
        return val
