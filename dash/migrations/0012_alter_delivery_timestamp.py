# Generated by Django 5.1.2 on 2024-11-23 02:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0011_rename_time_created_delivery_timestamp'),
    ]

    operations = [
        migrations.AlterField(
            model_name='delivery',
            name='timestamp',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
