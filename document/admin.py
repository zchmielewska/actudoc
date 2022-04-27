from django.contrib import admin

from document import models


@admin.register(models.Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "full_name", "code")


@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "company", "company_product_id", "name", "model")


@admin.register(models.Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "company", "company_category_id", "name")


@admin.register(models.Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("id", "company", "company_document_id", "title", "created_by", "created_at")
