# Generated by Django 4.2.15 on 2024-09-23 12:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0020_alter_productvariant_color_alter_productvariant_size'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventory',
            name='price',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
    ]
