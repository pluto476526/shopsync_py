# Generated by Django 5.1.2 on 2024-11-26 00:13

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0021_paymentmethod_shop'),
        ('shop', '0011_remove_cart_order_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paymentmethod',
            name='shop',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='shop.shop'),
        ),
    ]