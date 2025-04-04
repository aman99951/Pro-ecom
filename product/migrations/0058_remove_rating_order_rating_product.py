# Generated by Django 4.2.15 on 2024-10-08 06:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0057_discountcode_used_count'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='rating',
            name='order',
        ),
        migrations.AddField(
            model_name='rating',
            name='product',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='ratings', to='product.product'),
        ),
    ]
