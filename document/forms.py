from django import forms

from document import models


class DateInput(forms.DateInput):
    input_type = 'date'
    format = '%Y-%m-%d'


class DocumentForm(forms.ModelForm):
    class Meta:
        model = models.Document
        fields = ('product', 'category', 'validity_start', 'file')
        widgets = {
            'validity_start': forms.DateInput(attrs={'type': 'date'}),
        }


class RegisterForm(forms.Form):
    username = forms.CharField(max_length=36)
    password = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput, label="Repeat password")


class LoginForm(forms.Form):
    username = forms.CharField(max_length=36)
    password = forms.CharField(widget=forms.PasswordInput)
