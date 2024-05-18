import logging
from typing import Any

from django.core.validators import (
    MaxValueValidator,
    MinLengthValidator,
    MinValueValidator,
)
from django.forms import ValidationError
from products.models import Order
from rest_framework import serializers

from .models import Payment

log = logging.getLogger(__name__)


class PlasticCardSerializer(serializers.Serializer):
    """Serializer for validating and serializing plastic card data."""

    number = serializers.IntegerField(
        required=True,
        validators=[MinValueValidator(1), MaxValueValidator(99_999_999)],
    )
    name = serializers.CharField(
        required=True, max_length=255, validators=[MinLengthValidator(1)]
    )
    month = serializers.CharField(
        required=True, max_length=2, validators=[MinLengthValidator(2)]
    )
    year = serializers.IntegerField(
        required=True,
        validators=[MinValueValidator(1000), MaxValueValidator(9999)],
    )
    code = serializers.IntegerField(
        required=True,
        validators=[MinValueValidator(100), MaxValueValidator(999)],
    )

    def validate_month(self, value: Any) -> Any:
        """
        Validate the month field to ensure it represents an integer and is
        within the valid range (01-12).

        :param value: Month value to validate
        :type value: str
        :return: Validated month
        :rtype: str
        :raise ValidationError: If the value is not an integer or not within
            the valid month range.
        """
        try:
            int_value = int(value)
        except ValueError:
            raise ValidationError('Ensure this value is an integer')

        if not 1 <= int_value <= 12:
            raise ValidationError(
                'Ensure this value is a two-digit value from 01 to 12'
            )

        return value


class PaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for creating (and validating) payments based on order and card
    information.
    """

    class Meta:
        model = Payment
        fields = ['order_id', 'number', 'name', 'paid_sum']

    order_id = serializers.IntegerField(
        required=True,
        write_only=True,
        validators=[MinValueValidator(1)],
    )
    number = serializers.IntegerField(
        required=True,
        write_only=True,
        source='card_number',
        validators=[MinValueValidator(1), MaxValueValidator(99_999_999)],
    )
    name = serializers.CharField(
        required=True,
        write_only=True,
        max_length=255,
        validators=[MinLengthValidator(1)],
    )
    paid_sum = serializers.DecimalField(
        required=True,
        write_only=True,
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    def create(self, validated_data: dict) -> Payment:
        """
        Create a payment record based on validated data. Ensure the associated
        order is not archived.

        :param validated_data: Validated data for instance creation
        :type validated_data: dict
        :rtype: Payment
        :return: Payment instance
        :raise ValidationError: If the referenced order does not exist, is
            archived, or is not in the correct status for payment.
        """
        order_id = validated_data['order_id']
        order = Order.objects.filter(id=order_id, archived=False).first()
        if order is None:
            raise ValidationError(f'Order {order_id} does not exist')
        payment = Payment.objects.create(**validated_data)

        return payment
