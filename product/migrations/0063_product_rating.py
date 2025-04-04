# Generated by Django 4.2.15 on 2024-10-08 06:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0062_remove_rating_product_rating_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='Rating',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, related_name='products', to='product.rating'),
        ),
    ]
