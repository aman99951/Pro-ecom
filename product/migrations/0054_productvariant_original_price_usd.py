# Generated by Django 4.2.15 on 2024-10-05 12:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0053_discount'),
    ]

    operations = [
        migrations.AddField(
            model_name='productvariant',
            name='original_price_usd',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]
