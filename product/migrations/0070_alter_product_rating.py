# Generated by Django 4.2.15 on 2024-10-08 07:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0069_remove_rating_product'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='rating',
            field=models.PositiveIntegerField(default=4),
        ),
    ]
