# Generated by Django 4.2.15 on 2024-09-26 03:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0038_remove_product_taxes_delete_tax'),
    ]

    operations = [
        migrations.CreateModel(
            name='DynamicPriceField',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(help_text='Label for the additional charge', max_length=100)),
                ('value', models.DecimalField(decimal_places=2, help_text='Value of the additional charge', max_digits=10)),
            ],
        ),
    ]
