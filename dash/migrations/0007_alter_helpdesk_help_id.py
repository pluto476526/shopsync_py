# Generated by Django 5.1.3 on 2024-12-06 01:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0006_helpdesk_email_helpdesk_phone'),
    ]

    operations = [
        migrations.AlterField(
            model_name='helpdesk',
            name='help_id',
            field=models.CharField(blank=True, max_length=10, null=True, unique=True),
        ),
    ]