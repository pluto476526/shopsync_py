# Generated by Django 5.1.3 on 2024-12-06 02:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0007_alter_helpdesk_help_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='helpdesk',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
    ]
