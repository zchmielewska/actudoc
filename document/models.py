from django.conf import settings
from django.db import models


class Company(models.Model):
    name = models.CharField(max_length=100)


class Product(models.Model):
    # company = models.ForeignKey(Company, on_delete=models.CASCADE)
    name = models.CharField(max_length=60, verbose_name="name of insurance product")
    model = models.CharField(max_length=20, verbose_name="cash flow model")

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
        ordering = ["name"]


class Category(models.Model):
    # company = models.ForeignKey(Company, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

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
        ordering = ["name"]


class Document(models.Model):
    # company = models.ForeignKey(Company, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="insurance product")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="document category")
    validity_start = models.DateField(verbose_name="valid from")
    file = models.FileField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="create_user")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name

    def delete(self, *args, **kwargs):
        self.file.delete()
        super().delete(*args, **kwargs)

    class Meta:
        unique_together = ("product", "category", "validity_start")


class History(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    element = models.CharField(max_length=100)
    changed_from = models.CharField(max_length=100)
    changed_to = models.CharField(max_length=100)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="change_user")
    changed_at = models.DateTimeField(auto_now_add=True)
