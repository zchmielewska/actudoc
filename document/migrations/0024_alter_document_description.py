# Generated by Django 4.0.2 on 2022-04-10 10:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('document', '0023_alter_document_description'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
    ]
