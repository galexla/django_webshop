from django.db import migrations
from django.utils.translation import gettext_lazy as _


def add_configs(apps, schema_editor):
    ShopConfiguration = apps.get_model('configurations', 'ShopConfiguration')
    ShopConfiguration.objects.create(
        key='express_delivery_price',
        value='500',
        description=_('Express delivery price'),
    )
    ShopConfiguration.objects.create(
        key='ordinary_delivery_price',
        value='200',
        description=_('Ordinary delivery price'),
    )
    ShopConfiguration.objects.create(
        key='free_delivery_limit',
        value='2000',
        description=_('Minimum order value for free delivery'),
    )


class Migration(migrations.Migration):
    dependencies = [
        ('configurations', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_configs),
    ]
