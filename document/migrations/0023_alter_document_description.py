# Generated by Django 4.0.2 on 2022-04-10 10:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('document', '0022_document_description_document_title'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='description',
            field=models.TextField(null=True),
        ),
    ]
