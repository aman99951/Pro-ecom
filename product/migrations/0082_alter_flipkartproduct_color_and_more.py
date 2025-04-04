# Generated by Django 4.2.15 on 2024-10-26 12:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0081_remove_flipkartproduct_flipkart_id_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='flipkartproduct',
            name='color',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='flipkartproduct',
            name='image',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='flipkartproduct',
            name='size',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
