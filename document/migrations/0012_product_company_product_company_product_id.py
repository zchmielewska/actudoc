# Generated by Django 4.0.2 on 2022-02-27 08:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('document', '0011_alter_company_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='company',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='document.company'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='product',
            name='company_product_id',
            field=models.PositiveIntegerField(default=2),
            preserve_default=False,
        ),
    ]
