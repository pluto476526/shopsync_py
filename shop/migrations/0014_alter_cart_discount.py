# Generated by Django 5.1.3 on 2025-01-24 00:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0013_cartitem_is_deleted'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cart',
            name='discount',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
