from django import forms

from document import models


class DateInput(forms.DateInput):
    input_type = "date"
    format = "%Y-%m-%d"


class ProductForm(forms.ModelForm):
    class Meta:
        model = models.Product
        fields = ("name", "model",)


class CategoryForm(forms.ModelForm):
    class Meta:
        model = models.Category
        fields = ("name", )


class DocumentForm(forms.ModelForm):
    class Meta:
        model = models.Document
        fields = ("product", "category", "validity_start", "file")
        widgets = {
            "validity_start": forms.DateInput(attrs={"type": "date"}),
        }
