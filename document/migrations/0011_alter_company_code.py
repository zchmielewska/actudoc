# Generated by Django 4.0.2 on 2022-02-26 21:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('document', '0010_alter_company_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='company',
            name='code',
            field=models.CharField(max_length=32, unique=True),
        ),
    ]