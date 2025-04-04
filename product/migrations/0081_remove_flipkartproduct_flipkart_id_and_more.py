# Generated by Django 4.2.15 on 2024-10-26 12:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0080_ajioproduct_url'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='flipkartproduct',
            name='flipkart_id',
        ),
        migrations.RemoveField(
            model_name='flipkartproduct',
            name='product',
        ),
        migrations.RemoveField(
            model_name='flipkartproduct',
            name='stock',
        ),
        migrations.RemoveField(
            model_name='flipkartproduct',
            name='variant',
        ),
        migrations.AddField(
            model_name='flipkartproduct',
            name='brand',
            field=models.CharField(default=1, max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='flipkartproduct',
            name='color',
            field=models.CharField(default=1, max_length=50),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='flipkartproduct',
            name='image',
            field=models.URLField(default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='flipkartproduct',
            name='size',
            field=models.CharField(default=1, max_length=50),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='flipkartproduct',
            name='title',
            field=models.CharField(default=1, max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='flipkartproduct',
            name='url',
            field=models.URLField(default=1, max_length=500),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='flipkartproduct',
            name='price',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
    ]
