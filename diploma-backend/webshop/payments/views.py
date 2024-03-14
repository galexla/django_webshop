import logging
from random import randint
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from products.models import Order
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import PaymentModelSerializer, PaymentSerializer

log = logging.getLogger(__name__)


class PaymentView(LoginRequiredMixin, APIView):
    def post(self, request: Request, pk):
        order = get_object_or_404(Order, pk=pk, user=request.user)
        if order.status != order.STATUS_PROCESSING:
            msg = f'You can only pay for orders with status "{Order.STATUS_PROCESSING}".'
            return Response(
                {'status': [msg]}, status=status.HTTP_400_BAD_REQUEST
            )

        data = request.data
        serializer = PaymentSerializer(data=data)
        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        error = self._get_random_error(serializer.validated_data['number'])
        if error is not None:
            msg, status_ = error
            return Response({'non_field_errors': [msg]}, status=status_)

        data['paid_sum'] = order.total_cost
        response_body, status_ = self._try_save(order, data)

        return Response(response_body, status=status_)

    def _try_save(self, order, data) -> tuple[Any, int]:
        """Try to save. Return response body and HTTP status"""
        serializer = PaymentModelSerializer(data=data)
        if not serializer.is_valid():
            serializer.errors, status.HTTP_400_BAD_REQUEST

        try:
            with transaction.atomic():
                order.status = Order.STATUS_PAID
                order.save()
                serializer.save()
            msg = 'Order %s has been paid from card %s'
            log.info(msg, order.id, serializer.validated_data['card_number'])
            return None, status.HTTP_200_OK
        except IntegrityError:
            return None, status.HTTP_500_INTERNAL_SERVER_ERROR

    def _get_random_error(self, number) -> tuple[str, int] | None:
        """Return error message and HTTP status or None"""
        errors = (
            'Insufficient funds in your account',
            'Card has expired',
            'Card is blocked',
            'Incorrect card information',
            'Payment system is unavailable',
        )
        if number % 2 == 0 or number % 10 == 0:
            i_error = randint(0, len(errors) - 1)
            status_ = (
                status.HTTP_400_BAD_REQUEST
                if i_error <= 3
                else status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            return errors[i_error], status_

        return None
