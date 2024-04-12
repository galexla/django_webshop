from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response

from ..models import Product, Sale


def category_img_path(id, file_name):
    return f'/media/categories/category{id}/images/{file_name}'


def product_img_path(id, file_name):
    return f'/media/products/product{id}/images/{file_name}'


MONITOR_SHORT = {
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

MONITOR_SHORT_DB = {
    'title': 'Monitor',
    'price': '490.00',
    'count': 2,
    'created_at': '2024-01-30T15:30:48.823000Z',
    'description': 'Maecenas in nisi in eros sagittis sagittis eget in purus.',
    'free_delivery': 'False',
    'rating': '4.0',
}

MONITOR_SHORT_SRLZ = {
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


def get_ids(data):
    return [product['id'] for product in data]


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
        self.assertEqual(response.data['items'][0], MONITOR_SHORT)
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
        self.assertEqual(response.data[2], MONITOR_SHORT)

        monitor = MONITOR_SHORT_DB.copy()
        monitor['rating'] = '2.9'
        monitor['sold_count'] = 0
        ids_added = []
        for i in range(6):
            product = Product.objects.create(**monitor)
            ids_added.append(product.id)

        response = self.client.get(reverse('products:limited-products'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_ids(response.data), [1, 3, 4, 2] + ids_added[:4])
        monitor_srlz = MONITOR_SHORT_SRLZ.copy()
        monitor_srlz['rating'] = '2.9'
        response.data[3].pop('date')
        response.data[3].pop('id')
        self.assertEqual(response.data[3], monitor_srlz)


class LimitedProductsListViewTest(TestCase):
    fixtures = ['fixtures/sample_data.json']

    def test_all(self):
        response = self.client.get(reverse('products:limited-products'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_ids(response.data), [3, 4])
        self.assertEqual(response.data[1], MONITOR_SHORT)

        monitor = MONITOR_SHORT_DB.copy()
        monitor['is_limited_edition'] = True
        ids_added = []
        for i in range(20):
            product = Product.objects.create(**monitor)
            ids_added.append(product.id)

        response = self.client.get(reverse('products:limited-products'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_ids(response.data), [3, 4] + ids_added[:14])
        response.data[15].pop('date')
        response.data[15].pop('id')
        self.assertEqual(response.data[15], MONITOR_SHORT_SRLZ)


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
        self.assertEqual(response.data[2], MONITOR_SHORT)

        product = Product.objects.get(id=4)
        product.is_banner = False
        product.save()

        monitor = MONITOR_SHORT_DB.copy()
        monitor['is_banner'] = True
        ids_added = []
        for i in range(2):
            product = Product.objects.create(**monitor)
            ids_added.append(product.id)

        response = self.client.get(reverse('products:banners'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_ids(response.data), [1, 3] + ids_added[:1])
        response.data[2].pop('date')
        response.data[2].pop('id')
        self.assertEqual(response.data[2], MONITOR_SHORT_SRLZ)


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

        added_ids = []
        sale = Sale.objects.get(id=3)
        for i in range(10):
            sale.id = None
            sale.product_id = 1
            sale.save()
            added_ids.append(sale.product_id)

        ids = [1, 3, 4] + added_ids
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
