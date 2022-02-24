from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.views.generic.detail import DetailView

from account.forms import UserRegistrationForm, UserEditForm, ProfileEditForm
from account.models import Profile


class RegisterView(View):
    def get(self, request):
        user_form = UserRegistrationForm()
        return render(request, "account/register.html", {"user_form": user_form})

    def post(self, request):
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            new_user = user_form.save(commit=False)
            new_user.set_password(user_form.cleaned_data["password"])
            new_user.save()
            Profile.objects.create(user=new_user)
            return render(request, "account/register_done.html", {"new_user": new_user})
        return render(request, "account/register.html", {"user_form": user_form})


class EditProfileView(LoginRequiredMixin, View):
    def get(self, request):
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=request.user.profile)
        return render(request, "account/edit.html", {"user_form": user_form, "profile_form": profile_form})

    def post(self, request):
        user_form = UserEditForm(instance=request.user, data=request.POST)
        profile_form = ProfileEditForm(instance=request.user.profile, data=request.POST, files=request.FILES)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
        return render(request, "account/edit.html", {"user_form": user_form, "profile_form": profile_form})


class ProfileDetailView(LoginRequiredMixin, View):
    def get(self, request, username):
        user = get_object_or_404(User, username=username)
        return render(request, "account/profile_detail.html", {"user": user})
