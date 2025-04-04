# Generated by Django 4.2.15 on 2024-09-25 12:22

from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0033_remove_order_billing_address_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='cartitem',
            name='final_price',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10),
        ),
    ]
