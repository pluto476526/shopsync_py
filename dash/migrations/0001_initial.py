# Generated by Django 5.1.3 on 2025-01-04 14:28

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(max_length=50)),
                ('description', models.TextField(blank=True, null=True)),
                ('is_featured', models.BooleanField(default=False)),
                ('avatar', models.ImageField(default='dp1.jpg', upload_to='')),
                ('in_sale', models.BooleanField(default=False)),
                ('percent_off', models.PositiveIntegerField(default=0)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('total_sales', models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Coupon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('percent_off', models.PositiveIntegerField()),
                ('coupon_id', models.CharField(max_length=11, unique=True)),
                ('status', models.CharField(default='active', max_length=10)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('total_sales', models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Delivery',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('unregistered_user', models.CharField(blank=True, max_length=50, null=True)),
                ('order_number', models.CharField(max_length=10)),
                ('prod_id', models.CharField(max_length=10)),
                ('avatar', models.ImageField(default='dp1.jpg', upload_to='')),
                ('quantity', models.PositiveIntegerField()),
                ('price', models.PositiveIntegerField(default=0)),
                ('units', models.CharField(max_length=20)),
                ('discount', models.IntegerField(default=0)),
                ('status', models.CharField(default='processing', max_length=20)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('time_confirmed', models.DateTimeField(blank=True, null=True)),
                ('time_in_transit', models.DateTimeField(blank=True, null=True)),
                ('time_completed', models.DateTimeField(blank=True, null=True)),
                ('total', models.PositiveIntegerField(default=0)),
                ('phone', models.CharField(blank=True, max_length=15, null=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('county', models.CharField(default='Nairobi', max_length=20)),
                ('town', models.CharField(default='Nairobi', max_length=20)),
                ('address', models.CharField(blank=True, max_length=100, null=True)),
                ('instructions', models.TextField(blank=True, null=True)),
                ('source', models.CharField(default='dash', max_length=10)),
            ],
        ),
        migrations.CreateModel(
            name='Inventory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('avatar', models.ImageField(default='dp1.jpg', upload_to='')),
                ('product', models.CharField(max_length=50)),
                ('product_id', models.CharField(max_length=10, unique=True)),
                ('description', models.CharField(blank=True, max_length=250, null=True)),
                ('price', models.PositiveIntegerField()),
                ('units', models.CharField(blank=True, max_length=10, null=True)),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('status', models.CharField(default='available', max_length=20)),
                ('is_featured', models.BooleanField(default=False)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('in_deals', models.BooleanField(default=False)),
                ('in_discount', models.BooleanField(default=False)),
                ('in_sale', models.BooleanField(default=False)),
                ('discount', models.PositiveIntegerField(default=0)),
                ('percent_off', models.PositiveIntegerField(default=0)),
                ('available', models.BooleanField(default=False)),
                ('order_amount', models.PositiveIntegerField(default=0)),
                ('total_sales', models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='PaymentMethod',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payment_method', models.CharField(max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('identifier', models.CharField(max_length=10, null=True, unique=True)),
                ('avatar', models.ImageField(default='user.jpg', upload_to='')),
                ('in_staff', models.BooleanField(default=False)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('phone', models.CharField(blank=True, max_length=20, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comment', models.CharField(max_length=100)),
                ('body', models.TextField(blank=True, null=True)),
                ('rating', models.PositiveIntegerField(default=0)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role_name', models.CharField(max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='Supplier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='TodaysDeal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_id', models.CharField(max_length=10)),
                ('product', models.CharField(max_length=50, null=True)),
                ('avatar', models.ImageField(default='dp1.jpg', upload_to='')),
                ('discount', models.PositiveIntegerField(default=0)),
                ('time', models.DateTimeField(null=True)),
                ('status', models.CharField(default='active', max_length=10)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('total_sales', models.PositiveIntegerField(default=0)),
            ],
        ),
    ]
