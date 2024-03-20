import logging

from django.core.validators import MinValueValidator
from django.db import models
from django.forms import ValidationError

log = logging.getLogger(__name__)


class ShopConfiguration(models.Model):
    key = models.CharField(max_length=255, unique=True)
    value = models.CharField(max_length=255)
    description = models.TextField(blank=True, max_length=5000)

    protected_keys = [
        'ordinary_delivery_price',
        'express_delivery_price',
        'free_delivery_limit',
    ]

    def __str__(self):
        return self.key

    def clean_value(self):
        """
        Validates and converts 'value'. Raises ValidationError if
        validation fails.
        """
        try:
            float_value = float(self.value)
            MinValueValidator(0)(float_value)
            return float_value
        except (ValueError, ValidationError):
            raise ValidationError('Value must be a positive float number')

    def clean(self) -> None:
        self.clean_value()
        super().clean()

    def save(self, *args, **kwargs):
        if self.pk and self.key in self.protected_keys:
            original_key = ShopConfiguration.objects.get(pk=self.pk).key
            if self.key != original_key:
                log.info(
                    f'Renaming attempt blocked for protected configuration: {self.key}'
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


def get_shop_configuration(key: str):
    item = ShopConfiguration.objects.filter(key=key).first()
    if item is None:
        return 0
    return item.clean_value()


def get_all_shop_configurations() -> dict:
    items = ShopConfiguration.objects.all()
    return {item.key: item.clean_value() for item in items}
