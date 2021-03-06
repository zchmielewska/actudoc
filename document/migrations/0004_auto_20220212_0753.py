# Generated by Django 3.2.12 on 2022-02-12 07:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('document', '0003_product_company'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='company',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='document.company'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='document',
            name='company',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='document.company'),
            preserve_default=False,
        ),
    ]
