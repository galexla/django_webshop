import pytest
from django.db import IntegrityError
from django.forms import ValidationError
from tests.common import assert_not_raises

from ..models import (
    ShopConfiguration,
    get_all_shop_configurations,
    get_shop_configuration,
)


class TestShopConfiguration:
    @pytest.mark.parametrize(
        'should_be_ok, values',
        [
            (False, ['abc', '-1.123']),
            (True, ['1', 1, '1.123', 1.123]),
        ],
    )
    @pytest.mark.django_db(transaction=True)
    def test_clean_value_clean(self, should_be_ok, values):
        conf = ShopConfiguration()

        for value in values:
            conf.value = value
            if should_be_ok:
                assert isinstance(conf.clean_value(), float)
                with assert_not_raises(ValidationError):
                    conf.clean()
            else:
                with pytest.raises(ValidationError):
                    conf.clean_value()
                with pytest.raises(ValidationError):
                    conf.clean()

    @pytest.mark.parametrize(
        'key',
        [
            'ordinary_delivery_price',
            'express_delivery_price',
            'free_delivery_limit',
        ],
    )
    @pytest.mark.django_db(transaction=True)
    def test_rename_delete_protected(self, db_data, key):
        conf = ShopConfiguration.objects.get(key=key)

        with pytest.raises(ValidationError):
            conf.delete()

        conf.key += '123'
        with pytest.raises(ValidationError):
            conf.save()

    @pytest.mark.parametrize(
        'should_be_ok, key',
        [
            (True, 'abc'),
            (True, 'test'),
            (False, 'free_delivery_limit'),
        ],
    )
    @pytest.mark.django_db(transaction=True)
    def test_create(self, db_data, should_be_ok, key):
        if should_be_ok:
            with assert_not_raises(ValidationError):
                ShopConfiguration.objects.create(key=key, value='test')
        else:
            with pytest.raises(IntegrityError):
                ShopConfiguration.objects.create(key=key, value='test')

    @pytest.mark.parametrize(
        'key',
        [
            'ordinary_delivery_price',
            'express_delivery_price',
            'free_delivery_limit',
        ],
    )
    @pytest.mark.django_db(transaction=True)
    def test_update(self, db_data, key):
        conf = ShopConfiguration.objects.get(key=key)
        conf.value = '1.23'
        conf.save()
        conf.refresh_from_db()
        assert conf.value == '1.23'


@pytest.mark.django_db(transaction=True)
def test_get_shop_configuration(db_data):
    value = get_shop_configuration('ordinary_delivery_price')
    assert value == 200

    value = get_shop_configuration('free_delivery_limit')
    assert value == 2000


@pytest.mark.django_db(transaction=True)
def test_get_all_shop_configurations(db_data):
    confs = get_all_shop_configurations()
    expected_confs = {
        'express_delivery_price': 500,
        'ordinary_delivery_price': 200,
        'free_delivery_limit': 2000,
    }
    assert all(
        confs[key] == expected_confs[key] for key in expected_confs.keys()
    )
