import logging

from account.models import User
from django.contrib.auth.signals import user_logged_in
from django.db import IntegrityError, transaction
from django.dispatch import Signal, receiver
from rest_framework.request import Request

from .common import (
    fill_order_fields_if_needed,
    get_basket_by_cookie,
    get_basket_by_user,
    get_basket_id_cookie,
)
from .models import Basket, Order

log = logging.getLogger(__name__)


@receiver(user_logged_in)
def set_order_owner_by_basket_id(
    user: User, signal: Signal, request: Request, **kwargs
) -> None:
    """
    Get order by basket_id from cookies and assign an owner to it

    :param user: User instance
    :type user: User
    :param signal: Signal instance
    :type signal: Signal
    :param request: Request instance
    :type request: Request
    :return: None
    """
    basket_id = get_basket_id_cookie(request)
    orders = Order.objects.filter(
        basket_id=basket_id, user=None, status=Order.STATUS_NEW
    )
    orders.update(user=user, basket_id=None)
    for order in orders:
        fill_order_fields_if_needed(order, user)


@receiver(user_logged_in)
def switch_user_basket_if_needed(
    user: User, signal: Signal, request: Request, **kwargs
) -> None:
    """
    Set an existing basket as user's basket if user's basket doesn't exist or
    is empty.

    :param user: User instance
    :type user: User
    :param signal: Signal instance
    :type signal: Signal
    :param request: Request instance
    :type request: Request
    :return: None
    """
    basket_of_user: Basket = get_basket_by_user(user)
    basket_by_cookie: Basket = get_basket_by_cookie(request)

    if basket_of_user is None and basket_by_cookie is not None:
        basket_by_cookie.user = user
        basket_by_cookie.save()
        log.info('Set user %s basket to %s', user.id, basket_by_cookie.id)
    elif (
        basket_of_user is not None
        and basket_by_cookie is not None
        and basket_by_cookie.user is None
        and basket_by_cookie != basket_of_user
    ):
        n_products = len(basket_of_user.products.all())
        if n_products == 0:
            switch_user_basket(
                user, from_basket=basket_of_user, to_basket=basket_by_cookie
            )


def switch_user_basket(
    user: User, from_basket: Basket, to_basket: Basket
) -> bool:
    """
    Switch user's basket from one to another.

    :param user: User instance
    :type user: User
    :param from_basket: Basket instance to switch from
    :type from_basket: Basket
    :param to_basket: Basket instance to switch to
    :type to_basket: Basket
    :return: True if switched successfully, False otherwise
    :rtype: bool
    """
    try:
        with transaction.atomic():
            from_basket.delete()
            to_basket.user = user
            to_basket.save()
        log.info(
            'Switched user %s basket from %s to %s',
            user.id,
            from_basket.id,
            to_basket.id,
        )
        return True
    except IntegrityError:
        return False
