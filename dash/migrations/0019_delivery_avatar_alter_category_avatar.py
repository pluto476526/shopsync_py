# Generated by Django 5.1.2 on 2024-11-25 02:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0018_alter_inventory_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='delivery',
            name='avatar',
            field=models.ImageField(default='avatar5.png', upload_to=''),
        ),
        migrations.AlterField(
            model_name='category',
            name='avatar',
            field=models.ImageField(default='avatar5.png', upload_to=''),
        ),
    ]