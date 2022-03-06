from django import forms
from django.contrib.auth.models import User

from account.models import Profile


class LoginForm(forms.Form):
    email = forms.EmailField(label="E-mail address")
    password = forms.CharField(label="Password", widget=forms.PasswordInput)


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Repeat password", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name")

    def clean_password2(self):
        cd = self.cleaned_data
        if cd["password"] != cd["password2"]:
            raise forms.ValidationError("Passwords don\'t match.")
        return cd["password2"]


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")


class UserEditByAdminForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "is_active")


class ProfileEditByAdminForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("role",)
