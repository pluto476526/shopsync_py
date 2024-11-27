# Generated by Django 5.1.2 on 2024-11-23 01:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0009_delivery_time_completed_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='delivery',
            name='discount',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='delivery',
            name='price',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
        migrations.AlterField(
            model_name='delivery',
            name='quantity',
            field=models.PositiveIntegerField(),
        ),
        migrations.AlterField(
            model_name='delivery',
            name='total',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
    ]