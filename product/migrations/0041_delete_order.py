# Generated by Django 4.2.15 on 2024-09-26 04:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0040_cart_final_price'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Order',
        ),
    ]
