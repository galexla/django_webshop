import logging
from random import randint
from typing import Any

from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from products.models import Order
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import PaymentSerializer, PlasticCardSerializer

log = logging.getLogger(__name__)


class PaymentView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, pk):
        order = get_object_or_404(
            Order, pk=pk, user=request.user, archived=False
        )
        if order.status != order.STATUS_PROCESSING:
            msg = 'You can only pay for orders with status "{}".'.format(
                Order.STATUS_PROCESSING
            )
            return Response(
                {'non_field_errors': [msg]}, status=status.HTTP_400_BAD_REQUEST
            )

        data = request.data
        serializer = PlasticCardSerializer(data=data)
        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        card_number = serializer.validated_data['number']
        if card_number % 2 == 1 or card_number % 10 == 0:
            msg, http_status = self._get_random_error()
            return Response({'non_field_errors': [msg]}, status=http_status)

        data['order_id'] = order.id
        data['paid_sum'] = order.total_cost
        serializer = PaymentSerializer(data=data)
        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            order.status = Order.STATUS_PAID
            order.save()
            serializer.save()
        log.info('Order %s has been paid', order.id)

        return Response()

    def _get_random_error(self) -> tuple[str, int]:
        """Return random error message and HTTP status"""
        errors = (
            'Insufficient funds in your account',
            'Card has expired',
            'Card is blocked',
            'Incorrect card information',
            'Payment system is unavailable',
        )
        i_error = randint(0, len(errors) - 1)
        if i_error <= 3:
            return errors[i_error], status.HTTP_400_BAD_REQUEST
        else:
            return errors[i_error], status.HTTP_500_INTERNAL_SERVER_ERROR
