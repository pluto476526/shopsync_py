# Generated by Django 5.1.3 on 2025-01-04 14:28

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('dash', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ShopCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(max_length=30)),
            ],
        ),
        migrations.CreateModel(
            name='Shop',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('shopID', models.CharField(max_length=10, null=True, unique=True)),
                ('bio', models.TextField(blank=True, null=True)),
                ('logo', models.ImageField(default='logo.jpg', upload_to='')),
                ('dp1', models.ImageField(default='dp1.jpg', upload_to='')),
                ('dp2', models.ImageField(default='dp2.jpg', upload_to='')),
                ('dp3', models.ImageField(default='dp3.jpg', upload_to='')),
                ('title1', models.CharField(default='Find Top Brands.', max_length=50)),
                ('title2', models.CharField(default='Exceptional Quality.', max_length=50)),
                ('title3', models.CharField(default='Shop With Ease', max_length=50)),
                ('location', models.CharField(blank=True, max_length=20, null=True)),
                ('address', models.CharField(blank=True, max_length=100, null=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('phone', models.CharField(blank=True, max_length=15, null=True)),
                ('instagram', models.CharField(blank=True, max_length=50, null=True)),
                ('twitter', models.CharField(blank=True, max_length=50, null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('is_featured', models.BooleanField(default=False)),
                ('is_banned', models.BooleanField(default=False)),
                ('status', models.CharField(default='pending', max_length=20)),
                ('total_sales', models.PositiveIntegerField(default=0)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('shop_category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='shop_category', to='shop.shopcategory')),
            ],
        ),
        migrations.CreateModel(
            name='Cart',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cart_product_id', models.CharField(max_length=10)),
                ('category', models.CharField(max_length=50)),
                ('avatar', models.ImageField(default='dp1.jpg', upload_to='')),
                ('description', models.CharField(blank=True, max_length=255, null=True)),
                ('price', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('units', models.CharField(max_length=20)),
                ('quantity', models.PositiveIntegerField()),
                ('discount', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('total', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('status', models.CharField(default='pending', max_length=20)),
                ('time_ordered', models.DateTimeField(auto_now_add=True)),
                ('checked_out', models.DateTimeField(blank=True, null=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dash.inventory')),
                ('shop', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shop.shop')),
            ],
        ),
        migrations.CreateModel(
            name='ShopHelpDesk',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone', models.CharField(blank=True, max_length=15, null=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('issue', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('help_id', models.CharField(blank=True, max_length=10, null=True, unique=True)),
                ('status', models.CharField(default='pending', max_length=10)),
                ('is_sorted', models.BooleanField(default=False)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('admin', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='cc', to=settings.AUTH_USER_MODEL)),
                ('shop', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='shop', to='shop.shop')),
                ('username', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='shopper', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
