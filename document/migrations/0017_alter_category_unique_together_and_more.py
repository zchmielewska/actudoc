# Generated by Django 4.0.2 on 2022-02-28 19:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('document', '0016_document_company_document_id'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='category',
            unique_together={('company_category_id', 'company')},
        ),
        migrations.AlterUniqueTogether(
            name='product',
            unique_together={('company_product_id', 'company')},
        ),
    ]
