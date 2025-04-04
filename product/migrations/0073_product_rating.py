# Generated by Django 4.2.15 on 2024-10-08 07:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0072_remove_product_rating'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='rating',
            field=models.ForeignKey(blank=True, default=1, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='products', to='product.rating'),
        ),
    ]
