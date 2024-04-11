from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response


class TopLevelCategoryListViewTest(TestCase):
    fixtures = ['fixtures/sample_data.json']

    def test_get(self):
        response: Response = self.client.get(reverse('products:categories'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        path_start = '/media/categories/category'
        expected = [
            {
                'id': 1,
                'title': 'Phones, tablets, laptops and portable equipment',
                'image': {
                    'src': f'{path_start}1/image/mobile-devices.jpg',
                    'alt': 'some image alt',
                },
                'subcategories': [
                    {
                        'id': 3,
                        'title': 'Phones',
                        'image': {
                            'src': f'{path_start}3/image/smartphone.jpg',
                            'alt': 'monitor',
                        },
                    },
                    {
                        'id': 5,
                        'title': 'Laptops',
                        'image': {
                            'src': f'{path_start}5/image/laptop.jpg',
                            'alt': '',
                        },
                    },
                    {
                        'id': 6,
                        'title': 'Tablets',
                        'image': {
                            'src': f'{path_start}6/image/tablet.jpg',
                            'alt': '',
                        },
                    },
                ],
            },
            {
                'id': 2,
                'title': 'Computer, network and office equipment',
                'image': {
                    'src': f'{path_start}2/image/pc.jpg',
                    'alt': '',
                },
                'subcategories': [
                    {
                        'id': 4,
                        'title': 'Monitors',
                        'image': {
                            'src': f'{path_start}4/image/monitor.png',
                            'alt': '',
                        },
                    },
                    {
                        'id': 7,
                        'title': 'Printers',
                        'image': {
                            'src': f'{path_start}7/image/printer.jpg',
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

    def get_ids(self, data):
        return [product['id'] for product in data['items']]

    def test_all(self):
        url = reverse('products:catalog-list')

        response = self.get_filtered(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(response.data)
        self.assertEqual(response.data['currentPage'], 1)
        self.assertEqual(response.data['lastPage'], 1)
        self.assertEqual(self.get_ids(response.data), [4, 3, 1])

        response = self.get_filtered(url, name='mon')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.get_ids(response.data), [4])

        response = self.get_filtered(url, name='on')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.get_ids(response.data), [4, 3])

        response = self.get_filtered(
            url, maxPrice=800, available='false', sort='name', sortType='dec'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.get_ids(response.data), [2, 3, 4])

        response = self.get_filtered(
            url, minPrice=500, available='false', sort='rating'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.get_ids(response.data), [2, 3, 1])

        response = self.get_filtered(url, available='false', sort='date')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.get_ids(response.data), [1, 2, 3, 4])

        response = self.get_filtered(
            url, maxPrice=800, available='false', sort='reviews'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.get_ids(response.data), [2, 3, 4])
