# Generated by Django 5.1.3 on 2025-02-20 04:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0015_cart_coupon'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cart',
            name='cart_id',
        ),
        migrations.AddField(
            model_name='cart',
            name='status',
            field=models.CharField(default='pending', max_length=20),
        ),
    ]
