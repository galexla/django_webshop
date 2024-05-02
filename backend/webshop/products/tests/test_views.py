from decimal import Decimal

from account.models import User
from configurations.models import get_all_shop_configurations
from django.db import transaction
from django.test import TestCase
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APITestCase
from tests.common import (
    assert_dict_equal_exclude,
    get_attrs,
    get_ids,
    get_keys,
)
from tests.fixtures.products import (
    MONITOR_SHORT_DB_TPL,
    MONITOR_SHORT_SRLZD,
    MONITOR_SHORT_SRLZD_TPL,
    product_img_path,
)

from ..models import (
    Basket,
    BasketProduct,
    Order,
    OrderProduct,
    Product,
    Review,
    Sale,
)
from ..serializers import OrderSerializer
from ..views import BasketView, OrdersView, OrderView, basket_remove_products


def category_img_path(id, file_name):
    return f'/media/categories/category{id}/image/{file_name}'


class TopLevelCategoryListViewTest(TestCase):
    fixtures = ['fixtures/sample_data.json']

    def test_get(self):
        response: Response = self.client.get(reverse('products:categories'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected = [
            {
                'id': 1,
                'title': 'Phones, tablets, laptops and portable equipment',
                'image': {
                    'src': category_img_path(1, 'mobile-devices.jpg'),
                    'alt': 'some image alt',
                },
                'subcategories': [
                    {
                        'id': 3,
                        'title': 'Phones',
                        'image': {
                            'src': category_img_path(3, 'smartphone.jpg'),
                            'alt': 'monitor',
                        },
                    },
                    {
                        'id': 5,
                        'title': 'Laptops',
                        'image': {
                            'src': category_img_path(5, 'laptop.jpg'),
                            'alt': '',
                        },
                    },
                    {
                        'id': 6,
                        'title': 'Tablets',
                        'image': {
                            'src': category_img_path(6, 'tablet.jpg'),
                            'alt': '',
                        },
                    },
                ],
            },
            {
                'id': 2,
                'title': 'Computer, network and office equipment',
                'image': {
                    'src': category_img_path(2, 'pc.jpg'),
                    'alt': '',
                },
                'subcategories': [
                    {
                        'id': 4,
                        'title': 'Monitors',
                        'image': {
                            'src': category_img_path(4, 'monitor.png'),
                            'alt': '',
                        },
                    },
                    {
                        'id': 7,
                        'title': 'Printers',
                        'image': {
                            'src': category_img_path(7, 'printer.jpg'),
                            'alt': '',
                        },
                    },
                ],
            },
        ]
        self.assertEqual(response.data, expected)


class TagListViewSetTest(TestCase):
    fixtures = ['fixtures/sample_data.json']

    def test_all(self):
        url = reverse('products:tags-list')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected = [{'id': 1, 'name': 'Tag1'}, {'id': 2, 'name': 'Tag2'}]
        self.assertEqual(response.data, expected)

        response = self.client.get(url + '?category=1')
        self.assertEqual(response.data, expected)

        response = self.client.get(url + '?category=5')
        self.assertEqual(response.data, [{'id': 1, 'name': 'Tag1'}])

        response = self.client.get(url + '?category=6')
        self.assertEqual(response.data, [{'id': 2, 'name': 'Tag2'}])

        response = self.client.get(url + '?category=3')
        self.assertEqual(response.data, [])


class CatalogViewSetTest(TestCase):
    fixtures = ['fixtures/sample_data.json']

    def get_filtered(
        self,
        url,
        name='',
        minPrice=0,
        maxPrice=50000,
        freeDelivery='false',
        available='true',
        currentPage=1,
        sort='price',
        sortType='inc',
        tags=[],
        limit=20,
    ):
        """
        sort values: rating, price, reviews, date
        sortType values: inc, dec
        """
        filters = [
            f'filter[name]={name}',
            f'filter[minPrice]={minPrice}',
            f'filter[maxPrice]={maxPrice}',
            f'filter[freeDelivery]={freeDelivery}',
            f'filter[available]={available}',
            f'currentPage={currentPage}',
            f'sort={sort}',
            f'sortType={sortType}',
            f'limit={limit}',
        ]
        if tags:
            for tag in tags:
                filters.append(f'tags[]={tag}')

        return self.client.get(url + '?' + '&'.join(filters))

    def test_all(self):
        url = reverse('products:catalog-list')

        response = self.get_filtered(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['currentPage'], 1)
        self.assertEqual(response.data['lastPage'], 1)
        self.assertEqual(get_ids(response.data['items']), [4, 3, 1])

        response = self.get_filtered(url, name='mon')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_ids(response.data['items']), [4])

        response = self.get_filtered(url, name='on')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_ids(response.data['items']), [4, 3])
        self.assertEqual(response.data['items'][0], MONITOR_SHORT_SRLZD)
        self.assertEqual(response.data['items'][1]['title'], 'Smartphone')
        self.assertEqual(
            response.data['items'][1]['description'],
            'Nulla in libero volutpat, pellentesque erat eget, viverra nisi.',
        )

        response = self.get_filtered(
            url, maxPrice=800, available='false', sort='name', sortType='dec'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_ids(response.data['items']), [2, 3, 4])

        response = self.get_filtered(
            url, minPrice=500, available='false', sort='rating'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_ids(response.data['items']), [2, 3, 1])

        response = self.get_filtered(url, available='false', sort='date')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_ids(response.data['items']), [1, 2, 3, 4])

        response = self.get_filtered(
            url, maxPrice=800, available='false', sort='reviews'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_ids(response.data['items']), [2, 3, 4])


class PopularProductsListViewTest(TestCase):
    fixtures = ['fixtures/sample_data.json']

    def test_all(self):
        response = self.client.get(reverse('products:popular-products'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_ids(response.data), [1, 3, 4, 2])
        self.assertEqual(response.data[2], MONITOR_SHORT_SRLZD)

        monitor = MONITOR_SHORT_DB_TPL.copy()
        monitor['rating'] = '2.9'
        monitor['sold_count'] = 0
        ids_added = []
        for i in range(6):
            product = Product.objects.create(**monitor)
            ids_added.append(product.id)

        response = self.client.get(reverse('products:popular-products'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_ids(response.data), [1, 3, 4, 2] + ids_added[:4])
        assert_dict_equal_exclude(
            MONITOR_SHORT_SRLZD_TPL,
            response.data[7],
            ('id', 'date', 'rating'),
        )

        Product.objects.filter(id__in=ids_added).delete()


class LimitedProductsListViewTest(TestCase):
    fixtures = ['fixtures/sample_data.json']

    def test_all(self):
        response = self.client.get(reverse('products:limited-products'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_ids(response.data), [3, 4])
        self.assertEqual(response.data[1], MONITOR_SHORT_SRLZD)

        monitor = MONITOR_SHORT_DB_TPL.copy()
        monitor['is_limited_edition'] = True
        ids_added = []
        for i in range(20):
            product = Product.objects.create(**monitor)
            ids_added.append(product.id)

        response = self.client.get(reverse('products:limited-products'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_ids(response.data), [3, 4] + ids_added[:14])
        assert_dict_equal_exclude(
            MONITOR_SHORT_SRLZD_TPL,
            response.data[15],
            ('id', 'date'),
        )

        Product.objects.filter(id__in=ids_added).delete()


class BannerProductsListViewTest(TestCase):
    fixtures = ['fixtures/sample_data.json']

    def test_all(self):
        product = Product.objects.get(id=2)
        product.is_banner = False
        product.save()
        product = Product.objects.get(id=4)
        product.is_banner = True
        product.save()

        response = self.client.get(reverse('products:banners'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_ids(response.data), [1, 3, 4])
        self.assertEqual(response.data[2], MONITOR_SHORT_SRLZD)

        product = Product.objects.get(id=4)
        product.is_banner = False
        product.save()

        monitor = MONITOR_SHORT_DB_TPL.copy()
        monitor['is_banner'] = True
        ids_added = []
        for i in range(2):
            product = Product.objects.create(**monitor)
            ids_added.append(product.id)

        response = self.client.get(reverse('products:banners'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_ids(response.data), [1, 3] + ids_added[:1])
        self.assertTrue(
            MONITOR_SHORT_SRLZD_TPL.items() <= response.data[2].items()
        )

        Product.objects.filter(id__in=ids_added).delete()


class SalesViewTest(TestCase):
    fixtures = ['fixtures/sample_data.json']

    def test_all(self):
        response = self.client.get(reverse('products:sales'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_ids(response.data['items']), [1, 3, 4])
        self.assertEqual(
            response.data['items'][2],
            {
                'id': 4,
                'price': '490.00',
                'salePrice': '400.00',
                'dateFrom': '03-10',
                'dateTo': '12-31',
                'title': 'Monitor',
                'images': [
                    {'src': product_img_path(4, 'monitor.png'), 'alt': ''}
                ],
            },
        )
        self.assertEqual(response.data['currentPage'], 1)
        self.assertEqual(response.data['lastPage'], 1)

        id_products_added = []
        ids_added = []
        sale = Sale.objects.get(id=3)
        for i in range(10):
            sale.id = None
            sale.product_id = 1
            sale.save()
            id_products_added.append(sale.product_id)
            ids_added.append(sale.id)

        ids = [1, 3, 4] + id_products_added
        response = self.client.get(
            reverse('products:sales') + '?' + 'currentPage=2'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_ids(response.data['items']), ids[10:])

        response = self.client.get(
            reverse('products:sales') + '?' + 'currentPage=1'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_ids(response.data['items']), ids[:10])

        Sale.objects.filter(id__in=ids_added).delete()


class ProductDetailViewTest(TestCase):
    fixtures = ['fixtures/sample_data.json']

    monitor_srlzd = {
        'id': 4,
        'category': 4,
        'title': 'Monitor',
        'date': '2024-01-30T15:30:48.823000Z',
        'price': '490.00',
        'count': 2,
        'description': 'Maecenas in nisi in eros sagittis sagittis eget in purus.',
        'freeDelivery': 'False',
        'rating': '4.0',
        'tags': [{'id': 1, 'name': 'Tag1'}, {'id': 2, 'name': 'Tag2'}],
        'images': [{'src': product_img_path(4, 'monitor.png'), 'alt': ''}],
        'specifications': [{'name': 'Screen diagonal', 'value': '21"'}],
        'reviews': [
            {
                'id': 3,
                'author': 'Somebody',
                'email': 'somebody@email.net',
                'text': 'Has dead pixels',
                'rate': 1,
                'created_at': '2024-02-13T17:19:03.059000Z',
            },
            {
                'id': 2,
                'author': 'Susan',
                'email': 'susan@email.org',
                'text': 'Not bad',
                'rate': 4,
                'created_at': '2024-02-13T17:06:00.558000Z',
            },
            {
                'id': 1,
                'author': 'Jack',
                'email': 'jack@email.com',
                'text': 'An amazing monitor',
                'rate': 5,
                'created_at': '2024-02-13T17:04:23.462000Z',
            },
        ],
    }

    def test_all(self):
        response = self.client.get(
            reverse('products:product-details', kwargs={'pk': 4})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.monitor_srlzd.items() <= response.data.items())
        full_description = response.data.pop('fullDescription')
        self.assertEqual(response.data, self.monitor_srlzd)
        self.assertTrue(
            'sodales. Nam imperdiet quam at ullamcorper ullamcorper. Nulla'
            in full_description
        )


class PostTestCase(TestCase):
    def assert_all_invalid(
        self,
        url_lazy,
        ok_data: dict,
        field_name: str,
        values: list,
        expected_status,
    ):
        """
        Assert that all values of the specified field are invalid. None
        in values means the field is missing.
        """
        for value in values:
            data = ok_data.copy()
            if value is None:
                data.pop(field_name)
            else:
                data[field_name] = value
            response = self.client.post(url_lazy, data)
            self.assertEqual(response.status_code, expected_status)


class ReviewCreateViewTest(PostTestCase):
    fixtures = ['fixtures/sample_data.json']

    def test_post(self):
        ok_data = {
            'author': 'test',
            'email': 'test@test.com',
            'text': 'test',
            'rate': '5',
        }

        response = self.client.post(
            reverse('products:create-review', kwargs={'pk': 1}), ok_data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assert_all_invalid(
            reverse_lazy('products:create-review', kwargs={'pk': 1}),
            ok_data,
            'author',
            [None, '', 'a' * 201],
            status.HTTP_400_BAD_REQUEST,
        )

        self.assert_all_invalid(
            reverse_lazy('products:create-review', kwargs={'pk': 1}),
            ok_data,
            'email',
            [
                None,
                '',
                '@test.com',
                '#.,s@test.com',
                'test@',
                '@',
                'a' * 600 + '@test.com',
            ],
            status.HTTP_400_BAD_REQUEST,
        )

        self.assert_all_invalid(
            reverse_lazy('products:create-review', kwargs={'pk': 1}),
            ok_data,
            'text',
            [None, '', 'a' * 2001],
            status.HTTP_400_BAD_REQUEST,
        )

        self.assert_all_invalid(
            reverse_lazy('products:create-review', kwargs={'pk': 1}),
            ok_data,
            'rate',
            [None, '', 0, 6, 4.5],
            status.HTTP_400_BAD_REQUEST,
        )

        data = ok_data.copy()
        data['created_at'] = '2024-01-01T15:30:48.823000Z'
        self.client.post(
            reverse('products:create-review', kwargs={'pk': 1}), data
        )
        self.assertFalse(
            Review.objects.filter(
                created_at='2024-01-01T15:30:48.823000Z'
            ).exists()
        )

        Review.objects.filter(product_id=1).delete()


class BasketRemoveProductsTest(TestCase):
    fixtures = ['fixtures/sample_data.json']

    def test_basket_remove_products(self):
        basket_id = Basket.objects.get(user_id=1).id

        success = basket_remove_products(basket_id, {3: 1, 4: 1})
        self.assertTrue(success)
        basket_products = BasketProduct.objects.filter(basket_id=basket_id)
        self.assertEqual(len(basket_products), 1)
        self.assertEqual(basket_products[0].product_id, 4)
        self.assertEqual(basket_products[0].count, 1)

        success = basket_remove_products(basket_id, {3: 5, 4: 5})
        self.assertTrue(success)
        basket_products = BasketProduct.objects.filter(basket_id=basket_id)
        self.assertEqual(len(basket_products), 0)

    def test_basket_remove_all(self):
        basket_id = Basket.objects.get(user_id=1).id
        success = basket_remove_products(basket_id, {3: 1, 4: 2})
        self.assertTrue(success)
        basket_products = BasketProduct.objects.filter(basket_id=basket_id)
        self.assertEqual(len(basket_products), 0)

    def test_basket_decrement_non_existent(self):
        basket_id = Basket.objects.get(user_id=1).id
        success = basket_remove_products(basket_id, {1: 3, 2: 3})
        self.assertFalse(success)


class BasketViewTest(APITestCase):
    fixtures = ['fixtures/sample_data.json']

    def test_get(self):
        url = reverse('products:basket')
        user = User.objects.create(username='test', password='test')

        self.client.force_login(user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
        self.client.logout()

        admin = User.objects.get(username='admin')
        self.client.force_login(admin)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = get_keys(response.data, ['id', 'count'])
        self.assertListEqual(
            data, [{'id': 3, 'count': 1}, {'id': 4, 'count': 2}]
        )
        self.assertEqual(response.data[1], MONITOR_SHORT_SRLZD)
        self.client.logout()

        user.delete()

    def test_post(self):
        url = reverse('products:basket')
        user = User.objects.create(username='test', password='test')

        response = self.client.post(url, {'i': 4, 'count': 1})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.post(url, {'id': 4, 'count': -1})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.post(url, {'id': 0, 'count': 1})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.post(url, {'id': 4, 'count': 100})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsNotNone(response.cookies.get('basket_id'))
        basket_id = response.cookies['basket_id'].value
        self.assertNotEqual(basket_id, '')
        self.assertTrue(Basket.objects.filter(id=basket_id).exists())
        basket: Basket = Basket.objects.get(id=basket_id)
        self.assertIsNone(basket.user)
        self.assertAlmostEqual(
            basket.last_accessed.timestamp(),
            timezone.now().timestamp(),
            delta=3,
        )

        response = self.client.post(url, {'id': 3, 'count': 5})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.cookies['basket_id'].value, basket_id)
        self.assertListEqual(
            get_keys(response.data, ['id', 'count']),
            [{'id': 3, 'count': 5}],
        )
        self.assertListEqual(
            list(basket.basketproduct_set.values('product_id', 'count')),
            [{'product_id': 3, 'count': 5}],
        )

        response = self.client.post(url, {'id': 4, 'count': 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        assert_dict_equal_exclude(
            response.data[1], MONITOR_SHORT_SRLZD, ['count']
        )
        self.assertListEqual(
            get_keys(response.data, ['id', 'count']),
            [{'id': 3, 'count': 5}, {'id': 4, 'count': 1}],
        )
        self.assertListEqual(
            list(basket.basketproduct_set.values('product_id', 'count')),
            [{'product_id': 3, 'count': 5}, {'product_id': 4, 'count': 1}],
        )

        response = self.client.post(
            reverse('account:sign-in'),
            {'username': 'test', 'password': 'test'},
        )
        response = self.client.get(url)
        self.assertListEqual(
            get_keys(response.data, ['id', 'count']),
            [{'id': 3, 'count': 5}, {'id': 4, 'count': 1}],
        )
        response = self.client.post(reverse('account:sign-out'))

        response = self.client.post(
            reverse('account:sign-in'),
            {'username': 'test', 'password': 'test'},
        )
        response = self.client.get(url)
        self.assertListEqual(
            get_keys(response.data, ['id', 'count']),
            [{'id': 3, 'count': 5}, {'id': 4, 'count': 1}],
        )
        assert_dict_equal_exclude(
            response.data[1], MONITOR_SHORT_SRLZD, ['count']
        )
        self.assertListEqual(
            list(basket.basketproduct_set.values('product_id', 'count')),
            [{'product_id': 3, 'count': 5}, {'product_id': 4, 'count': 1}],
        )

        user.delete()

    def test_get_products(self):
        basket = Basket.objects.get(user__username='admin')
        view = BasketView()
        products = view._get_products(basket)
        self.assertListEqual(
            get_attrs(products, ['id', 'count']),
            [{'id': 3, 'count': 1}, {'id': 4, 'count': 2}],
        )

        basket = Basket(user_id=10)
        products = view._get_products(basket)
        self.assertListEqual(products, [])

    def test_get_response(self):
        basket = Basket.objects.get(user__username='admin')
        view = BasketView()
        products = view._get_products(basket)
        response = view._get_response(products, basket.id.hex)
        self.assertEqual(response.cookies['basket_id'].value, basket.id.hex)
        self.assertEqual(response.data[1], MONITOR_SHORT_SRLZD)

        response = view._get_response([], basket.id.hex)
        self.assertEqual(response.data, [])

        response = view._get_response([], '')
        self.assertEqual(response.data, [])

    def test_set_cookie(self):
        view = BasketView()
        response = Response()
        view._set_cookie(response, '123')
        self.assertEqual(response.cookies['basket_id'].value, '123')
        view._set_cookie(response, 'abc')
        self.assertEqual(response.cookies['basket_id'].value, 'abc')

    def test_add_products(self):
        basket = Basket.objects.create()
        view = BasketView()

        product = Product.objects.get(id=1)
        self.assertFalse(view._add_products(basket.id.hex, product, 6))
        self.assertEqual(basket.basketproduct_set.count(), 0)

        self.assertTrue(view._add_products(basket.id.hex, product, 3))
        basket.refresh_from_db()
        self.assertEqual(basket.basketproduct_set.count(), 1)
        self.assertEqual(basket.basketproduct_set.all()[0].product_id, 1)
        self.assertEqual(basket.basketproduct_set.all()[0].count, 3)

        self.assertFalse(view._add_products(basket.id.hex, product, 3))
        basket.refresh_from_db()
        self.assertEqual(basket.basketproduct_set.count(), 1)
        self.assertEqual(basket.basketproduct_set.all()[0].product_id, 1)
        self.assertEqual(basket.basketproduct_set.all()[0].count, 3)

        self.assertTrue(view._add_products(basket.id.hex, product, 2))
        basket.refresh_from_db()
        self.assertEqual(basket.basketproduct_set.count(), 1)
        self.assertEqual(basket.basketproduct_set.all()[0].product_id, 1)
        self.assertEqual(basket.basketproduct_set.all()[0].count, 5)

    def test_delete(self):
        url = reverse('products:basket')

        response = self.client.delete(url, {'i': 4, 'count': 1})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.delete(url, {'id': 4, 'count': -1})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.delete(url, {'id': 0, 'count': 1})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.delete(url, {'id': 1, 'count': 1})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(url, {'id': 3, 'count': 5})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.post(url, {'id': 1, 'count': 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        basket = Basket.objects.get(id=response.cookies['basket_id'].value)
        self.assertEqual(basket.basketproduct_set.count(), 2)
        self.assertListEqual(
            list(basket.basketproduct_set.values('product_id', 'count')),
            [{'product_id': 1, 'count': 2}, {'product_id': 3, 'count': 5}],
        )
        response = self.client.delete(url, {'id': 1, 'count': 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.delete(url, {'id': 3, 'count': 4})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(basket.basketproduct_set.count(), 1)
        self.assertListEqual(
            list(basket.basketproduct_set.values('product_id', 'count')),
            [{'product_id': 3, 'count': 1}],
        )

        admin = User.objects.get(username='admin')
        self.client.force_login(admin)

        response = self.client.delete(url, {'id': 0, 'count': 1})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.delete(url, {'id': 4, 'count': 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        assert_dict_equal_exclude(
            response.data[1], MONITOR_SHORT_SRLZD, ['count']
        )
        basket = Basket.objects.get(user_id=admin.id)
        self.assertEqual(basket.basketproduct_set.count(), 2)
        self.assertListEqual(
            list(basket.basketproduct_set.values('product_id', 'count')),
            [{'product_id': 3, 'count': 1}, {'product_id': 4, 'count': 1}],
        )

        response = self.client.delete(url, {'id': 4, 'count': 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(basket.basketproduct_set.count(), 1)
        self.assertListEqual(
            list(basket.basketproduct_set.values('product_id', 'count')),
            [{'product_id': 3, 'count': 1}],
        )

        response = self.client.delete(url, {'id': 3, 'count': 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(basket.basketproduct_set.count(), 0)
        self.assertListEqual(
            list(basket.basketproduct_set.values('product_id', 'count')), []
        )


def fill_template(template: dict, **kwargs):
    result = template.copy()
    for field, value in kwargs.items():
        result[field] = value
    return result


class OrdersViewTest(APITestCase):
    fixtures = ['fixtures/sample_data.json']

    NEW_ORDER_TPL = {
        'id': 4,
        'user_id': 3,
        'full_name': '',
        'email': '',
        'phone': '',
        'delivery_type': '',
        'payment_type': '',
        'total_cost': Decimal('2578.00'),
        'status': Order.STATUS_NEW,
        'city': '',
        'address': '',
        'archived': False,
    }

    def test_get(self):
        url = reverse('products:orders')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        admin = User.objects.get(username='admin')
        self.client.force_login(admin)

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_ids(response.data), [3, 2])
        expected_order1 = {
            'id': 3,
            'createdAt': '2024.03.02 19:16:12',
            'fullName': 'Nick',
            'email': 'kva@kva.com',
            'phone': '+712334361',
            'deliveryType': Order.DELIVERY_ORDINARY,
            'paymentType': Order.PAYMENT_SOMEONE,
            'totalCost': '1979.00',
            'status': Order.STATUS_PROCESSING,
            'city': 'Moscow',
            'address': 'Sretensky blvd 1',
        }
        assert_dict_equal_exclude(
            response.data[0], expected_order1, ['products']
        )
        assert_dict_equal_exclude(
            response.data[0]['products'][1],
            MONITOR_SHORT_SRLZD,
            ['count'],
        )
        self.assertEqual(len(response.data[0]['products']), 2)
        self.assertEqual(response.data[0]['products'][0]['id'], 3)
        self.assertEqual(response.data[0]['products'][0]['count'], 1)
        self.assertEqual(response.data[0]['products'][1]['id'], 4)
        self.assertEqual(response.data[0]['products'][1]['count'], 2)
        self.client.logout()

        user = User.objects.create(username='test', password='test')
        self.client.force_login(user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_ids(response.data), [])

        user.delete()

    def test_post(self):
        url = reverse('products:orders')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        user = User.objects.create(username='test', password='test')
        self.client.force_login(user)

        response = self.client.post(url, {'id': 1, 'count': 1})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.post(url, [{'i': 1, 'count': 1}])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.post(url, [{'id': 1, 'c': 1}])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.post(url, [{'id': 1, 'count': 0}])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.post(url, [])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.post(
            url, [{'id': 2, 'count': 2}, {'id': 4, 'count': 2}]
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(
            url, [{'id': 3, 'count': 2}, {'id': 4, 'count': 2}]
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data.get('orderId'))
        order_id = response.data['orderId']
        self.assertTrue(Order.objects.filter(id=order_id).exists())
        order = list(Order.objects.filter(id=order_id).values())
        expected_order = fill_template(
            self.NEW_ORDER_TPL, user_id=user.id, total_cost=Decimal('2578.00')
        )
        assert_dict_equal_exclude(
            order[0], expected_order, ['id', 'created_at']
        )
        product_counts = list(
            OrderProduct.objects.filter(order_id=order_id).values(
                'product_id', 'count'
            )
        )
        self.assertListEqual(
            product_counts,
            [{'product_id': 3, 'count': 2}, {'product_id': 4, 'count': 2}],
        )
        self.client.logout()

        admin = User.objects.get(username='admin')
        self.client.force_login(admin)

        Product.objects.filter(id__in=[3, 4]).update(count=10)
        response = self.client.post(
            url, [{'id': 3, 'count': 1}, {'id': 4, 'count': 1}]
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        basket = Basket.objects.get(user_id=admin.id)
        product_counts = list(
            basket.basketproduct_set.values('product_id', 'count')
        )
        self.assertListEqual(product_counts, [{'product_id': 4, 'count': 1}])

        user.delete()

    def test_are_available(self):
        view = OrdersView()

        self.assertFalse(view._are_available({3: 8, 4: 2}))
        self.assertFalse(view._are_available({3: 7, 4: 3}))
        self.assertTrue(view._are_available({3: 7, 4: 2}))

        Product.objects.filter(id=3).update(archived=True)
        self.assertFalse(view._are_available({3: 7, 4: 2}))

    def test_create_order(self):
        view = OrdersView()
        user = User.objects.create(
            username='test',
            password='test',
            first_name='Kva',
            last_name='Test',
            email='test@test.com',
        )
        user.profile.phone = '+1234567'
        user.profile.save()

        self.client.force_login(user)
        success = False
        with transaction.atomic():
            order: Order = view._create_order({3: 7, 4: 2}, user)
            success = True
        self.assertTrue(success)
        order = Order.objects.get(id=order.id)
        expected_order = fill_template(
            self.NEW_ORDER_TPL,
            user_id=user.id,
            total_cost=Decimal('6573.00'),
            full_name=user.get_full_name(),
            email=user.email,
            phone=user.profile.phone,
        )
        assert_dict_equal_exclude(
            order.__dict__,
            expected_order,
            ['id', 'created_at', '_state'],
        )
        product_counts = list(
            order.orderproduct_set.values('product_id', 'count')
        )
        self.assertListEqual(
            product_counts,
            [{'product_id': 3, 'count': 7}, {'product_id': 4, 'count': 2}],
        )
        products = Product.objects.filter(id__in=[3, 4])
        self.assertListEqual(
            list(products.values('count', 'sold_count')),
            [{'count': 0, 'sold_count': 12}, {'count': 0, 'sold_count': 6}],
        )

        user.delete()

    def test_add_products(self):
        view = OrdersView()
        user = User.objects.get(username='12')
        self.client.force_login(user)

        order = Order.objects.create(user_id=user.id)
        products = {3: 3, 4: 2, 1: 1}
        view._add_products(order.id, products)
        product_counts = list(
            order.orderproduct_set.values('product_id', 'count')
        )
        expected_product_counts = [
            {'product_id': 3, 'count': 3},
            {'product_id': 4, 'count': 2},
            {'product_id': 1, 'count': 1},
        ]
        self.assertListEqual(
            product_counts,
            expected_product_counts,
        )


class OrderViewTest(APITestCase):
    fixtures = ['fixtures/sample_data.json']

    def test_get(self):
        url = reverse('products:order', kwargs={'pk': 3})

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        admin = User.objects.get(username='admin')
        self.client.force_login(admin)

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_order = {
            'id': 3,
            'createdAt': '2024.03.02 19:16:12',
            'fullName': 'Nick',
            'email': 'kva@kva.com',
            'phone': '+712334361',
            'deliveryType': Order.DELIVERY_ORDINARY,
            'paymentType': Order.PAYMENT_SOMEONE,
            'totalCost': '1979.00',
            'status': Order.STATUS_PROCESSING,
            'city': 'Moscow',
            'address': 'Sretensky blvd 1',
        }
        assert_dict_equal_exclude(response.data, expected_order, ['products'])
        assert_dict_equal_exclude(
            response.data['products'][1],
            MONITOR_SHORT_SRLZD,
            ['count'],
        )
        self.assertEqual(len(response.data['products']), 2)
        self.assertEqual(response.data['products'][0]['id'], 3)
        self.assertEqual(response.data['products'][0]['count'], 1)
        self.assertEqual(response.data['products'][1]['id'], 4)
        self.assertEqual(response.data['products'][1]['count'], 2)
        self.client.logout()

        user = User.objects.create(username='test', password='test')
        self.client.force_login(user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        user.delete()

    def test_post(self):
        url = reverse('products:order', kwargs={'pk': 3})

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        user = User.objects.create(username='test', password='test')
        self.client.force_login(user)

        response = self.client.post(url, {'status': 'new'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # create a new order
        response = self.client.post(
            reverse('products:orders'), [{'id': 4, 'count': 2}]
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order_id = response.data['orderId']
        url = reverse('products:order', kwargs={'pk': order_id})
        order = Order.objects.get(id=order_id)

        # test: if order.status == Order.STATUS_PROCESSING...
        order.status = Order.STATUS_PROCESSING
        order.save()
        order_data_before = order.__dict__
        post_data = {k: '' for k in order_data_before.keys()}
        response = self.client.post(url, post_data)
        order.refresh_from_db()
        order_data_after = order.__dict__
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        assert_dict_equal_exclude(
            order_data_before, order_data_after, ['_state']
        )
        self.assertEqual(response.data, {'orderId': order_id})

        # test: if order.status != Order.STATUS_NEW...
        order.status = Order.STATUS_NEW
        order.save()
        order_data = {
            'fullName': 'Nick',
            'email': 'kva@kva.com',
            'phone': '+712334361',
            'deliveryType': Order.DELIVERY_ORDINARY,
            'paymentType': Order.PAYMENT_SOMEONE,
            'status': Order.STATUS_PROCESSING,
            'totalCost': 0,
            'city': 'Moscow',
            'address': 'Sretensky blvd 1',
        }
        response = self.client.post(url, order_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.data, {'orderId': order_id})
        order = Order.objects.get(id=order_id)
        serializer = OrderSerializer(instance=order)
        assert_dict_equal_exclude(
            order_data,
            serializer.data,
            ['id', 'orderId', 'createdAt', 'totalCost', 'products'],
        )
        order.refresh_from_db()
        self.assertEqual(order.total_cost, 1180)

        # test posting invalid data
        order.status = Order.STATUS_NEW
        order.save()
        post_data = order_data.copy()
        post_data.pop('fullName')
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_delivery_cost(self):
        shop_confs = get_all_shop_configurations()
        order = Order.objects.get(id=3)
        view = OrderView()

        delivery_cost = view._get_delivery_cost(
            order.id, Order.DELIVERY_EXPRESS, 200
        )
        self.assertEqual(delivery_cost, shop_confs['express_delivery_price'])
        delivery_cost = view._get_delivery_cost(
            order.id, Order.DELIVERY_EXPRESS, 0
        )
        self.assertEqual(delivery_cost, shop_confs['express_delivery_price'])

        delivery_cost = view._get_delivery_cost(
            order.id,
            Order.DELIVERY_ORDINARY,
            shop_confs['free_delivery_limit'] - 1,
        )
        self.assertEqual(delivery_cost, shop_confs['ordinary_delivery_price'])
        delivery_cost = view._get_delivery_cost(
            order.id,
            Order.DELIVERY_ORDINARY,
            shop_confs['free_delivery_limit'],
        )
        self.assertEqual(delivery_cost, 0)

        order.products.update(free_delivery=1)
        delivery_cost = view._get_delivery_cost(
            order.id,
            Order.DELIVERY_ORDINARY,
            shop_confs['free_delivery_limit'] - 1,
        )
        self.assertEqual(delivery_cost, 0)
        delivery_cost = view._get_delivery_cost(
            order.id,
            Order.DELIVERY_ORDINARY,
            shop_confs['free_delivery_limit'],
        )
        self.assertEqual(delivery_cost, 0)

    def test_is_delivery_free(self):
        order = Order.objects.get(id=3)
        view = OrderView()

        is_delivery_free = view._is_delivery_free(
            order.id, Order.DELIVERY_EXPRESS
        )
        self.assertEqual(is_delivery_free, False)
        is_delivery_free = view._is_delivery_free(
            order.id, Order.DELIVERY_ORDINARY
        )
        self.assertEqual(is_delivery_free, False)

        order.products.update(free_delivery=1)
        is_delivery_free = view._is_delivery_free(
            order.id, Order.DELIVERY_EXPRESS
        )
        self.assertEqual(is_delivery_free, False)
        is_delivery_free = view._is_delivery_free(
            order.id, Order.DELIVERY_ORDINARY
        )
        self.assertEqual(is_delivery_free, True)
