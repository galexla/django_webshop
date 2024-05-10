from decimal import Decimal

from django.core.validators import (
    MaxValueValidator,
    MinLengthValidator,
    MinValueValidator,
)
from django.db import models
from products.models import Order


class Payment(models.Model):
    order = models.OneToOneField(
        Order, on_delete=models.CASCADE, related_name='payment'
    )
    card_number = models.IntegerField(
        blank=False,
        validators=[MinValueValidator(1), MaxValueValidator(99_999_999)],
    )
    name = models.CharField(
        blank=False, max_length=255, validators=[MinLengthValidator(1)]
    )
    paid_sum = models.DecimalField(
        blank=False,
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal(0))],
    )
    paid_at = models.DateTimeField(blank=False, auto_now_add=True)
