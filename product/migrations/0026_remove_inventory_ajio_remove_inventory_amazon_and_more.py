# Generated by Django 4.2.15 on 2024-09-24 11:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0025_shippingaddress_billingaddress'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='inventory',
            name='ajio',
        ),
        migrations.RemoveField(
            model_name='inventory',
            name='amazon',
        ),
        migrations.RemoveField(
            model_name='inventory',
            name='flipkart',
        ),
        migrations.RemoveField(
            model_name='inventory',
            name='myntra',
        ),
    ]
