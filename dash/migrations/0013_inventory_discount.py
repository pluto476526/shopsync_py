# Generated by Django 5.1.2 on 2024-11-24 10:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0012_alter_delivery_timestamp'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventory',
            name='discount',
            field=models.IntegerField(default=0),
        ),
    ]