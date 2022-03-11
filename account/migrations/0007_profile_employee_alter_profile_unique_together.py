# Generated by Django 4.0.2 on 2022-03-08 06:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('document', '0019_alter_document_file'),
        ('account', '0006_profile_account_pro_user_id_90d36a_idx'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='employee',
            field=models.PositiveIntegerField(default=1),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='profile',
            unique_together={('company', 'employee')},
        ),
    ]