from typing import Iterable

from account.models import User
from django.test import TestCase
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response

from ..models import Basket, BasketProduct, Product, Review, Sale
from ..views import BasketView, basket_decrement


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


def get_ids(data: Iterable[dict]) -> list:
    return [item['id'] for item in data]


def get_obj_ids(data: Iterable[object]) -> list:
    return [item.id for item in data]


def product_img_path(id, file_name):
    return f'/media/products/product{id}/images/{file_name}'


# a version of monitor entity serialized with ProductShortSerializer,
# 'fullDescription' is omitted
MONITOR_SHORT_SRLZD = {
    'id': 4,
    'title': 'Monitor',
    'price': '490.00',
    'count': 2,
    'date': '2024-01-30T15:30:48.823000Z',
    'description': 'Maecenas in nisi in eros sagittis sagittis eget in purus.',
    'freeDelivery': 'False',
    'rating': '4.0',
    'category': 4,
    'reviews': 3,
    'images': [
        {
            'src': product_img_path(4, 'monitor.png'),
            'alt': '',
        }
    ],
    'tags': [{'id': 1, 'name': 'Tag1'}, {'id': 2, 'name': 'Tag2'}],
}

# template based on monitor, field names are taken from the database
MONITOR_SHORT_DB_TMPL = {
    'title': 'Monitor',
    'price': '490.00',
    'count': 2,
    'created_at': '2024-01-30T15:30:48.823000Z',
    'description': 'Maecenas in nisi in eros sagittis sagittis eget in purus.',
    'free_delivery': 'False',
    'rating': '4.0',
}

# template based on monitor, serialized with ProductShortSerializer
MONITOR_SHORT_SRLZD_TMPL = {
    'category': None,
    'title': 'Monitor',
    'price': '490.00',
    'count': 2,
    'description': 'Maecenas in nisi in eros sagittis sagittis eget in purus.',
    'freeDelivery': 'False',
    'rating': '4.0',
    'reviews': 0,
    'tags': [],
    'images': [{'src': '/media/products/goods_icon.png', 'alt': ''}],
}


def assertDictEqualExclude(test_case: TestCase, dict1, dict2, exclude_keys):
    dict1 = dict1.copy()
    dict2 = dict2.copy()
    for key in exclude_keys:
        dict1.pop(key, None)
        dict2.pop(key, None)
    test_case.assertDictEqual(dict1, dict2)


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

        monitor = MONITOR_SHORT_DB_TMPL.copy()
        monitor['rating'] = '2.9'
        monitor['sold_count'] = 0
        ids_added = []
        for i in range(6):
            product = Product.objects.create(**monitor)
            ids_added.append(product.id)

        response = self.client.get(reverse('products:popular-products'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_ids(response.data), [1, 3, 4, 2] + ids_added[:4])
        assertDictEqualExclude(
            self,
            MONITOR_SHORT_SRLZD_TMPL,
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

        monitor = MONITOR_SHORT_DB_TMPL.copy()
        monitor['is_limited_edition'] = True
        ids_added = []
        for i in range(20):
            product = Product.objects.create(**monitor)
            ids_added.append(product.id)

        response = self.client.get(reverse('products:limited-products'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_ids(response.data), [3, 4] + ids_added[:14])
        assertDictEqualExclude(
            self,
            MONITOR_SHORT_SRLZD_TMPL,
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

        monitor = MONITOR_SHORT_DB_TMPL.copy()
        monitor['is_banner'] = True
        ids_added = []
        for i in range(2):
            product = Product.objects.create(**monitor)
            ids_added.append(product.id)

        response = self.client.get(reverse('products:banners'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_ids(response.data), [1, 3] + ids_added[:1])
        self.assertDictContainsSubset(
            MONITOR_SHORT_SRLZD_TMPL, response.data[2]
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
        self.assertDictContainsSubset(self.monitor_srlzd, response.data)
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


class TopLevelFunctionsTest(TestCase):
    fixtures = ['fixtures/sample_data.json']

    def test_basket_decrement(self):
        basket_id = Basket.objects.get(user_id=1).id

        success = basket_decrement(basket_id, {3: 1, 4: 1})
        self.assertTrue(success)
        basket_products = BasketProduct.objects.filter(basket_id=basket_id)
        self.assertEqual(len(basket_products), 1)
        self.assertEqual(basket_products[0].product_id, 4)
        self.assertEqual(basket_products[0].count, 1)

        success = basket_decrement(basket_id, {3: 5, 4: 5})
        self.assertTrue(success)
        basket_products = BasketProduct.objects.filter(basket_id=basket_id)
        self.assertEqual(len(basket_products), 0)

    def test_basket_remove_all(self):
        basket_id = Basket.objects.get(user_id=1).id
        success = basket_decrement(basket_id, {3: 1, 4: 2})
        self.assertTrue(success)
        basket_products = BasketProduct.objects.filter(basket_id=basket_id)
        self.assertEqual(len(basket_products), 0)

    def test_basket_decrement_non_existent(self):
        basket_id = Basket.objects.get(user_id=1).id
        success = basket_decrement(basket_id, {1: 3, 2: 3})
        self.assertFalse(success)


def get_keys(data: Iterable[dict], keys: Iterable) -> list[dict]:
    result = []
    for item in data:
        elem = {}
        for key in keys:
            elem[key] = item.get(key)
        result.append(elem)
    return result


def get_attrs(data: Iterable[object], attrs: Iterable) -> list[dict]:
    result = []
    for item in data:
        elem = {}
        for key in attrs:
            elem[key] = getattr(item, key, None)
        result.append(elem)
    return result


class BasketViewTest(TestCase):
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
        basket.refresh_from_db()
        self.assertListEqual(
            list(basket.basketproduct_set.values('product_id', 'count')),
            [{'product_id': 3, 'count': 5}],
        )

        response = self.client.post(url, {'id': 1, 'count': 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertListEqual(
            get_keys(response.data, ['id', 'count']),
            [{'id': 1, 'count': 1}, {'id': 3, 'count': 5}],
        )
        basket.refresh_from_db()
        self.assertListEqual(
            list(basket.basketproduct_set.values('product_id', 'count')),
            [{'product_id': 1, 'count': 1}, {'product_id': 3, 'count': 5}],
        )

        response = self.client.post(
            reverse('account:sign-in'),
            {'username': 'test', 'password': 'test'},
        )
        response = self.client.get(url)
        self.assertListEqual(
            get_keys(response.data, ['id', 'count']),
            [{'id': 1, 'count': 1}, {'id': 3, 'count': 5}],
        )
        response = self.client.post(reverse('account:sign-out'))

        response = self.client.post(
            reverse('account:sign-in'),
            {'username': 'test', 'password': 'test'},
        )
        response = self.client.get(url)
        self.assertListEqual(
            get_keys(response.data, ['id', 'count']),
            [{'id': 1, 'count': 1}, {'id': 3, 'count': 5}],
        )
        basket.refresh_from_db()
        self.assertListEqual(
            list(basket.basketproduct_set.values('product_id', 'count')),
            [{'product_id': 1, 'count': 1}, {'product_id': 3, 'count': 5}],
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

