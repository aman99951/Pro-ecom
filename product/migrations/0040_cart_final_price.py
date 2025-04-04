# Generated by Django 4.2.15 on 2024-09-26 04:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0039_dynamicpricefield'),
    ]

    operations = [
        migrations.AddField(
            model_name='cart',
            name='final_price',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
    ]
