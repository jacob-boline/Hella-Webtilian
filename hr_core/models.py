# hr_core/models.py

from django.db import models


class PendingVariant(models.Model):
    recipe_key = models.CharField(max_length=32, db_index=True)
    src_name = models.TextField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True, db_index=True)
    attempts = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["recipe_key", "src_name"], name="uq_pending_variant_recipe_src"),
        ]

    def __str__(self) -> str:
        status = "processed" if self.processed_at else "pending"
        return f"{self.recipe_key}:{self.src_name} ({status})"
