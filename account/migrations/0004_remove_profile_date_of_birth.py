# Generated by Django 4.0.2 on 2022-02-26 21:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0003_profile_company'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='date_of_birth',
        ),
    ]
