# Generated by Django 4.0.2 on 2022-02-24 19:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('document', '0004_auto_20220212_0753'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='company',
        ),
    ]