# Generated by Django 4.0.2 on 2022-02-24 19:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('document', '0005_remove_product_company'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='category',
            name='company',
        ),
    ]
