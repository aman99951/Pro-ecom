# Generated by Django 4.2.15 on 2024-09-24 14:28

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('product', '0028_myntraproduct_flipkartproduct_amazonproduct_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='billingaddress',
            old_name='street_address',
            new_name='address_1',
        ),
        migrations.RenameField(
            model_name='shippingaddress',
            old_name='street_address',
            new_name='address_1',
        ),
        migrations.RemoveField(
            model_name='billingaddress',
            name='profile',
        ),
        migrations.RemoveField(
            model_name='shippingaddress',
            name='profile',
        ),
        migrations.AddField(
            model_name='billingaddress',
            name='address_2',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='billingaddress',
            name='address_type',
            field=models.CharField(choices=[('home', 'Home'), ('work', 'Work'), ('other', 'Other')], default='home', max_length=20),
        ),
        migrations.AddField(
            model_name='billingaddress',
            name='user',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='shippingaddress',
            name='address_2',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='shippingaddress',
            name='address_type',
            field=models.CharField(choices=[('home', 'Home'), ('work', 'Work'), ('other', 'Other')], default='home', max_length=20),
        ),
        migrations.AddField(
            model_name='shippingaddress',
            name='user',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
