import logging
from datetime import timedelta

from account.models import User
from django.utils import timezone
from rest_framework.request import Request

from .models import Basket, Order
from .serializers import BasketIdSerializer

log = logging.getLogger(__name__)


def get_basket(request: Request) -> Basket | None:
    """
    Get basket by user or cookie

    :param request: Request
    :type request: Request
    :return: Basket
    :rtype: Basket | None
    """
    user: User = request.user
    basket = get_basket_by_user(user)
    if not basket:
        basket = get_basket_by_cookie(request)
        if not basket:
            return None
        elif not can_access_basket(basket, user):
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
    """
    Get basket by user

    :param user: User
    :type user: User | None
    :return: Basket
    :rtype: Basket | None
    """
    if user is None or user.is_anonymous:
        return None

    return Basket.objects.filter(user=user).first()


def get_basket_id_cookie(request: Request) -> str:
    """
    Get basket id saved in cookie

    :param request: Request
    :type request: Request
    :return: basket id
    :rtype: str
    """
    return request.COOKIES.get('basket_id')


def get_basket_by_cookie(request: Request) -> Basket | None:
    """
    Get basket by cookie

    :param request: Request
    :type request: Request
    :return: Basket
    :rtype: Basket | None
    """
    basket_id = get_basket_id_cookie(request)
    serializer = BasketIdSerializer(data={'basket_id': basket_id})
    if not serializer.is_valid():
        return None

    return Basket.objects.filter(
        id=serializer.validated_data['basket_id']
    ).first()


def get_client_ip(request: Request) -> str:
    """
    Get client IP address

    :param request: Request
    :type request: Request
    :return: IP address
    :rtype: str
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def can_access_basket(basket: Basket, user: User) -> bool:
    """
    Check if user has permissions to access basket

    :param basket: Basket
    :type basket: Basket
    :param user: User
    :type user: User
    :return: True if user has permissions to access basket
    :rtype: bool
    """
    if basket.user and basket.user != user:
        return False
    return True


def update_basket_access_time(basket: Basket) -> None:
    """
    Update basket last access time

    :param basket: Basket
    :type basket: Basket
    :return: None
    """
    update_after = timedelta(seconds=120)
    now = timezone.now()
    if now - update_after > basket.last_accessed:
        basket.save()  # update basket.last_accessed


def delete_unused_baskets(max_age: int) -> None:
    """
    Delete too old baskets with no user assigned

    :param max_age: Max age in seconds
    :type max_age: int
    :return: None
    """
    Basket.objects.filter(
        last_accessed__lt=timezone.now() - timedelta(seconds=max_age),
        user__isnull=True,
    ).delete()


def fill_order_fields_if_needed(order: Order, user: User) -> None:
    """
    Fill some empty order fields from a user instance

    :param order: request
    :type order: Order
    :param user: user to get fields from
    :type order: User
    :return: None
    """
    if order.full_name == '':
        order.full_name = user.get_full_name()

    if order.phone == '':
        order.phone = user.profile.phone or ''

    if order.email == '':
        order.email = user.email or ''
