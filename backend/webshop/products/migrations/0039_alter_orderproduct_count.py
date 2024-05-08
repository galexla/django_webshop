# Generated by Django 4.2.11 on 2024-05-08 19:02

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0038_alter_basketproduct_count'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderproduct',
            name='count',
            field=models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)]),
        ),
    ]
