from tests.common import product_img_path

# a version of monitor entity serialized with ProductDetailSerializer,
# 'fullDescription' field is omitted
MONITOR_DETAIL_SRLZD = {
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
            'date': '2024-02-13 17:19',
        },
        {
            'id': 2,
            'author': 'Susan',
            'email': 'susan@email.org',
            'text': 'Not bad',
            'rate': 4,
            'date': '2024-02-13 17:06',
        },
        {
            'id': 1,
            'author': 'Jack',
            'email': 'jack@email.com',
            'text': 'An amazing monitor',
            'rate': 5,
            'date': '2024-02-13 17:04',
        },
    ],
}

# a version of monitor entity serialized with ProductShortSerializer,
# 'fullDescription' field is omitted
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
MONITOR_SHORT_DB_TPL = {
    'title': 'Monitor',
    'price': '490.00',
    'count': 2,
    'created_at': '2024-01-30T15:30:48.823000Z',
    'description': 'Maecenas in nisi in eros sagittis sagittis eget in purus.',
    'free_delivery': 'False',
    'rating': '4.0',
}

# template based on monitor, serialized with ProductShortSerializer
MONITOR_SHORT_SRLZD_TPL = {
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

INVALID_EMAILS = [
    'a@' + 'a' * 260 + '.com',
    'test',
    'test@test',
    '.test@test.com',
]

VALID_EMAILS = [
    'test@test.com',
    'a@a.com',
    'test.test@test.com',
    'a_test@test.com',
]

INVALID_PHONES = ['+' + '1' * 32, '+1234', '1234567']

VALID_PHONES = ['+' + '1' * 31, '+12345', '+1234567']
