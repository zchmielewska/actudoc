from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


def validate_file_extension(value):
    if value.file.content_type != 'application/pdf':
        raise ValidationError(u'Only PDF files can be uploaded.')


class Company(models.Model):
    name = models.CharField(max_length=32, unique=True)
    full_name = models.CharField(max_length=100)
    code = models.CharField(max_length=32, unique=True)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        indexes = [models.Index(fields=["name", ])]


class Product(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    company_product_id = models.PositiveIntegerField()
    name = models.CharField(max_length=60, verbose_name="name of insurance product",
                            help_text="E.g. Term Life Insurance")
    model = models.CharField(max_length=20, verbose_name="cash flow model", help_text="E.g. TERM02")

    def __str__(self):
        return f"{self.name} ({self.model})"

    def delete(self, *args, **kwargs):
        documents = self.document_set.all()
        files = [document.file for document in documents]
        for file in files:
            file.delete()
        super().delete(*args, **kwargs)

    def number_of_documents(self):
        return self.document_set.count()

    class Meta:
        indexes = [models.Index(fields=["company", "company_product_id"])]
        ordering = ["id"]
        unique_together = ("company_product_id", "company")


class Category(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    company_category_id = models.PositiveIntegerField()
    name = models.CharField(max_length=100, help_text="E.g. Terms and conditions or Technical description")

    def __str__(self):
        return self.name

    def delete(self, *args, **kwargs):
        documents = self.document_set.all()
        files = [document.file for document in documents]
        for file in files:
            file.delete()
        super().delete(*args, **kwargs)

    def number_of_documents(self):
        return self.document_set.count()

    class Meta:
        indexes = [models.Index(fields=["company", "company_category_id"])]
        ordering = ["id"]
        unique_together = ("company_category_id", "company")


def document_path(instance, filename):
    return f"{instance.company.name}/{filename}"


class Document(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    company_document_id = models.PositiveIntegerField()
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="insurance product")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="document category")
    validity_start = models.DateField(verbose_name="valid from")
    file = models.FileField(upload_to=document_path, validators=[validate_file_extension])
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="create_user")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name

    def delete(self, *args, **kwargs):
        self.file.delete()
        super().delete(*args, **kwargs)

    def slug(self):
        return f"{self.company.name}-{self.company_document_id}"

    class Meta:
        indexes = [models.Index(fields=["company", "company_document_id"])]
        unique_together = ("company", "product", "category", "validity_start")


class History(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    element = models.CharField(max_length=100)
    changed_from = models.CharField(max_length=100)
    changed_to = models.CharField(max_length=100)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="change_user")
    changed_at = models.DateTimeField(auto_now_add=True)
