# Generated by Django 5.1.3 on 2025-01-04 10:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0010_inventory_order_instructions'),
    ]

    operations = [
        migrations.RenameField(
            model_name='paymentmethod',
            old_name='payment_method',
            new_name='method',
        ),
    ]
