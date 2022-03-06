from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.views import View

from account.forms import LoginForm, RegistrationForm, UserEditForm, UserEditByAdminForm, ProfileEditByAdminForm
from account.models import Profile
from document.models import Company


class LoginView(View):
    """
    View to log in.

    To log in, user should provide e-mail address and password.
    The default Django authentication has been adjusted to accept e-mail rather than username.
    """
    def get(self, request):
        form = LoginForm()
        return render(request, "account/login.html", {"form": form})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            user = authenticate(username=email, password=password)

            if user is not None:
                if user.is_active:
                    login(request, user)
                    url_next = request.GET.get("next", "/")
                    return redirect(url_next)
                else:
                    form.add_error("email", "Account is blocked.")
            else:
                form.add_error("email", "Incorrect email or password.")
        return render(request, "account/login.html", {"form": form})


class RegisterView(View):
    def get(self, request):
        form = RegistrationForm()
        return render(request, "account/register.html", {"form": form})

    def post(self, request):
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # Data for a new user
            new_user = form.save(commit=False)
            new_user.username = str(User.objects.count() + 1)
            new_user.set_password(form.cleaned_data["password"])

            # User can either create an account for a new company...
            if request.POST.get("company") == "new_company":
                code = get_random_string(length=32)
                company = Company.objects.create(
                    name=request.POST.get("company_short_name"),
                    full_name=request.POST.get("company_full_name"),
                    code=code,
                )
                new_user.is_staff = True

            # ...or join as a member of an existing company
            if request.POST.get("company") == "existing_company":
                try:
                    code = request.POST.get("company_code")
                    company = Company.objects.get(code=code)
                except Company.DoesNotExist:
                    messages.error(request, "Incorrect company code!")
                    return render(request, "account/register.html", {"form": form})

            # Data for a person is contained in two models: User and Profile
            new_user.save()
            Profile.objects.create(user=new_user, company=company)

            return render(request, "account/register_done.html", {"new_user": new_user})
        return render(request, "account/register.html", {"form": form})


class EditProfileView(LoginRequiredMixin, View):
    def get(self, request):
        user_form = UserEditForm(instance=request.user)
        return render(request, "account/edit.html", {"user_form": user_form})

    def post(self, request):
        user_form = UserEditForm(instance=request.user, data=request.POST)
        if user_form.is_valid():
            user_form.save()
            return redirect(reverse("account:profile_detail", kwargs={"username": request.user.username}))
        return render(request, "account/edit.html", {"user_form": user_form})


class ProfileDetailView(LoginRequiredMixin, View):
    def get(self, request, username):
        user = get_object_or_404(User, username=username)
        return render(request, "account/profile_detail.html", {"user": user})


class UserListView(LoginRequiredMixin, View):
    def get(self, request):
        company = request.user.profile.company
        profiles = Profile.objects.filter(company=company)
        users = [profile.user for profile in profiles]
        return render(request, "account/list_users.html", {"users": users})


class EditUserByAdminView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.profile.role == "admin"

    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        if user.profile.company.name != request.user.profile.company.name:
            raise PermissionDenied

        user_form = UserEditByAdminForm(instance=user)
        profile_form = ProfileEditByAdminForm(instance=user.profile)

        if user.is_staff:
            user_form.fields["is_active"].disabled = True
            profile_form.fields["role"].disabled = True

        return render(request, "account/edit_by_admin.html", {"user_form": user_form, "profile_form": profile_form})

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        if user.profile.company.name != request.user.profile.company.name:
            raise PermissionDenied

        user_form = UserEditByAdminForm(instance=user, data=request.POST)
        profile_form = ProfileEditByAdminForm(instance=user.profile, data=request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect(reverse("account:user_list"))
        return render(request, "account/edit.html", {"user_form": user_form})
