from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.models import User

from account.models import Profile


class LoginForm(forms.Form):
    email = forms.EmailField(label="E-mail address")
    password = forms.CharField(label="Password", widget=forms.PasswordInput)


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(label="Password", widget=forms.PasswordInput, min_length=8)
    password2 = forms.CharField(label="Repeat password", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name")

    def clean_password(self):
        password = self.cleaned_data.get('password')
        try:
            password_validation.validate_password(password, self.instance)
        except forms.ValidationError as error:
            self.add_error("password", error)
        return password

    def clean_password2(self):
        password = self.cleaned_data["password"]
        password2 = self.cleaned_data["password2"]
        if password != password2:
            raise forms.ValidationError("Passwords don\'t match.")
        return password2


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
