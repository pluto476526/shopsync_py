# Generated by Django 5.1.2 on 2024-11-22 00:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0002_alter_inventory_description_alter_inventory_units'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventory',
            name='price',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]