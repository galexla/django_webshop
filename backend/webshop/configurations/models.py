from django.core.validators import MinValueValidator
from django.db import models
from django.forms import ValidationError


class ShopConfiguration(models.Model):
    """
    Model to keep global shop configuration values.

    Attributes:
        key (str): Configuration key.
        value (str): Configuration value.
        description (str): Configuration description.
        protected_keys (list[str]): List of keys that cannot be deleted or
            renamed.
    """

    key = models.CharField(max_length=255, unique=True)
    value = models.CharField(max_length=255)
    description = models.TextField(blank=True, max_length=5000)

    protected_keys = [
        'ordinary_delivery_price',
        'express_delivery_price',
        'free_delivery_limit',
    ]

    def __str__(self) -> str:
        """
        Return key.

        :return: Key
        :rtype: str
        """
        return self.key

    def clean_value(self) -> float:
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
        """
        Save configuration, restrict renaming of protected keys.

        :return: None
        """
        if self.pk and self.key in self.protected_keys:
            original_key = ShopConfiguration.objects.get(pk=self.pk).key
            if self.key != original_key:
                return

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Delete configuration if key is not protected.

        :return: None
        """
        if self.key in self.protected_keys:
            return

        super().delete(*args, **kwargs)


def get_shop_configuration(key: str) -> float:
    item = ShopConfiguration.objects.filter(key=key).first()
    if item is None:
        return 0
    return item.clean_value()


def get_all_shop_configurations() -> dict:
    """
    Get all shop configurations.

    :return: Dictionary with configuration keys as keys and values as values
    :rtype: dict
    """
    items = ShopConfiguration.objects.all()
    return {item.key: item.clean_value() for item in items}
