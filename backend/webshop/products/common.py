import logging
from datetime import timedelta

from account.models import User
from django.utils import timezone
from rest_framework.request import Request

from .models import Basket
from .serializers import BasketIdSerializer

log = logging.getLogger(__name__)


def get_basket(request: Request) -> Basket | None:
    user: User = request.user
    basket = get_basket_by_user(user)
    if not basket:
        basket = get_basket_by_cookie(request)
        if not basket:
            return None
        elif not is_basket_owner(basket, user):
            log.warning(
                'User %s [%s] attempts to retrieve basket of user %s',
                getattr(user, 'id', None),
                get_client_ip(request),
                basket.user_id,
            )
            return None

    if basket:
        update_basket_access_time(basket)

    return basket


def get_basket_by_user(user: User | None) -> Basket | None:
    if user is None or user.is_anonymous:
        return None

    return Basket.objects.filter(user=user).first()


def get_basket_by_cookie(request: Request) -> Basket | None:
    basket_id = request.COOKIES.get('basket_id')
    serializer = BasketIdSerializer(data={'basket_id': basket_id})
    if not serializer.is_valid():
        return None

    return Basket.objects.filter(
        id=serializer.validated_data['basket_id']
    ).first()


def get_client_ip(request: Request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def is_basket_owner(basket: Basket, user: User) -> bool:
    if user.is_anonymous:
        return basket.user is None
    return basket.user == user


def update_basket_access_time(basket: Basket) -> None:
    """Update basket last access time"""
    update_after = timedelta(seconds=120)
    now = timezone.now()
    if now - update_after > basket.last_accessed:
        basket.save()  # update basket.last_accessed
