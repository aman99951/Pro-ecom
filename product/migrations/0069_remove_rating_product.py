# Generated by Django 4.2.15 on 2024-10-08 07:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0068_rating_product_alter_product_rating'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='rating',
            name='product',
        ),
    ]
