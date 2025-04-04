# Generated by Django 4.2.15 on 2024-10-22 13:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0076_remove_agent_user_agent_name_agent_password_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='amazonproduct',
            name='amazon_id',
        ),
        migrations.RemoveField(
            model_name='amazonproduct',
            name='product',
        ),
        migrations.RemoveField(
            model_name='amazonproduct',
            name='stock',
        ),
        migrations.RemoveField(
            model_name='amazonproduct',
            name='variant',
        ),
        migrations.AddField(
            model_name='amazonproduct',
            name='brand',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='amazonproduct',
            name='color',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='amazonproduct',
            name='image',
            field=models.URLField(default=1, max_length=500),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='amazonproduct',
            name='size',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='amazonproduct',
            name='title',
            field=models.CharField(default=1, max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='amazonproduct',
            name='url',
            field=models.URLField(default=1, max_length=500),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='amazonproduct',
            name='price',
            field=models.CharField(max_length=50),
        ),
    ]
