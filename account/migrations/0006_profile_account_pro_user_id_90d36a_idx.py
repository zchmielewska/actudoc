# Generated by Django 4.0.2 on 2022-03-08 06:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0005_alter_profile_company'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='profile',
            index=models.Index(fields=['user'], name='account_pro_user_id_90d36a_idx'),
        ),
    ]
