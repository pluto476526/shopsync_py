# Generated by Django 5.1.3 on 2024-12-07 00:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0004_helpdesk_admin_profile_identifier_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='helpdesk',
            name='status',
            field=models.CharField(default='pending', max_length=10),
        ),
    ]
