# Generated by Django 5.1.3 on 2025-01-04 10:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0005_alter_inventory_price'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventory',
            name='quantity',
            field=models.PositiveIntegerField(),
        ),
    ]
