# Generated by Django 5.1.3 on 2025-01-17 06:46

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0004_townsshipped'),
    ]

    operations = [
        migrations.AddField(
            model_name='cart',
            name='town',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='shop.townsshipped'),
        ),
    ]
