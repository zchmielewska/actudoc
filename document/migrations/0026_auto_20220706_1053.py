# Generated by Django 3.2.13 on 2022-07-06 08:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('document', '0025_alter_document_unique_together'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='document',
            name='product',
        ),
        migrations.AddField(
            model_name='document',
            name='product',
            field=models.ManyToManyField(to='document.Product', verbose_name='insurance product'),
        ),
    ]
