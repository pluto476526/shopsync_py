# Generated by Django 5.1.2 on 2024-11-24 20:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0006_alter_cart_checked_out'),
    ]

    operations = [
        migrations.RenameField(
            model_name='cart',
            old_name='timestamp',
            new_name='time_ordered',
        ),
    ]