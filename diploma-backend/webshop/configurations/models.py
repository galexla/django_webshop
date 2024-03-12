import logging

from django.db import models

log = logging.getLogger(__name__)


class ShopConfiguration(models.Model):
    key = models.CharField(max_length=255, unique=True)
    value = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    protected_keys = [
        'regular_delivery_price',
        'express_delivery_price',
        'free_delivery_limit',
    ]

    def __str__(self):
        return self.key

    def save(self, *args, **kwargs):
        if self.pk and self.key in self.protected_keys:
            original_key = ShopConfiguration.objects.get(pk=self.pk).key
            if self.key != original_key:
                log.info(
                    f'Modification attempt blocked for protected configuration: {self.key}'
                )
                return

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.key in self.protected_keys:
            log.info(
                f'Deletion attempt blocked for protected configuration: {self.key}'
            )
            return

        super().delete(*args, **kwargs)
