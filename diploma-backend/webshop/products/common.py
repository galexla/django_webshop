import logging
from datetime import datetime, timedelta, timezone

from account.models import User
from rest_framework.request import Request

from .models import Basket
from .serializers import BasketIdSerializer

log = logging.getLogger(__name__)


def get_basket(request: Request) -> Basket | None:
    user: User = request.user
    basket = get_basket_by_user(user)
    if basket is None:
        basket = get_basket_by_cookie(request)
        if not check_basket_permissions(basket, request):
            return None

    if basket:
        update_basket_access_time(basket)

    return basket


def get_basket_by_user(user: User) -> Basket | None:
    if user is None or user.is_anonymous:
        return None

    queryset = Basket.objects.filter(user=user).all()
    return queryset[0] if queryset else None


def get_basket_by_cookie(request: Request) -> Basket | None:
    basket_id = request.COOKIES.get('basket_id')
    serializer = BasketIdSerializer(data={'basket_id': basket_id})
    if not serializer.is_valid():
        return None

    queryset = Basket.objects.filter(
        id=serializer.validated_data['basket_id']
    ).all()
    return queryset[0] if queryset else None


def get_client_ip(request: Request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def check_basket_permissions(basket: Basket, request: Request) -> bool:
    user = request.user
    if basket and basket.user and basket.user != user:
        ip = get_client_ip(request)
        user_id = user.id if user else None
        log.warning(
            f'User {user_id} [{ip}] attempts to retrieve basket of user {basket.user_id}'
        )
        return False
    return True


def update_basket_access_time(basket: Basket) -> None:
    """Update basket last access time"""
    update_after = timedelta(seconds=120)
    # TODO: get current timezone?
    now = datetime.now(timezone(timedelta(0)))
    if now - update_after > basket.last_accessed:
        basket.save()  # update basket.last_accessed
