# Generated by Django 5.1.2 on 2024-11-21 15:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventory',
            name='description',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AlterField(
            model_name='inventory',
            name='units',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
    ]
