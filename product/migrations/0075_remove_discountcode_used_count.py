# Generated by Django 4.2.15 on 2024-10-11 15:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0074_remove_product_rating_rating_product'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='discountcode',
            name='used_count',
        ),
    ]
