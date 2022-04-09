# Generated by Django 4.0.2 on 2022-04-09 17:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('document', '0021_alter_document_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='description',
            field=models.TextField(default='a'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='document',
            name='title',
            field=models.CharField(default='b', max_length=128),
            preserve_default=False,
        ),
    ]
