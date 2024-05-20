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
        """
        Clean value and return as float.

        :raises ValidationError: If value isn't parsable to non-negative float
        :return: Value as float
        :rtype: float
        """
        try:
            float_value = float(self.value)
        except ValueError:
            raise ValidationError('Value must be a non-negative float number')

        MinValueValidator(0)(float_value)
        return float_value

    def clean(self) -> None:
        """
        Clean value before saving.

        :return: None
        """
        self.clean_value()
        super().clean()

    def save(self, *args, **kwargs) -> None:
        """
        Save configuration, restrict renaming of protected keys.

        :return: None
        """
        if self.pk:
            prev_key = ShopConfiguration.objects.get(pk=self.pk).key
            if prev_key in self.protected_keys and self.key != prev_key:
                raise ValidationError('Unable to rename a protected key')

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs) -> None:
        """
        Delete configuration if key is not protected.

        :return: None
        """
        if self.key in self.protected_keys:
            raise ValidationError('Unable to delete a protected key')

        super().delete(*args, **kwargs)


def get_shop_configuration(key: str) -> float:
    """
    Get shop configuration value by key.

    :param key: Configuration key
    :type key: str
    :return: Configuration value
    :rtype: float
    """
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
