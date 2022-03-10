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
    The default Django authentication has been adjusted to accept e-mail rather than username (see authentication.py).

    Access company: all
    Access roles: all
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
    """
    View to register.

    The app uses e-mail address to authenticate so username is a consecutive number.
    There are two ways to register:
    - create a new company account,
    - join to an existing company by providing registration code.

    If the user creates the new company, he gets a role of admin and is part of is_staff.
    User with is_staff can not be non-admin or inactive.

    Access company: all
    Access roles: all
    """
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
                    name=request.POST.get("company_short_name").lower(),
                    full_name=request.POST.get("company_full_name"),
                    code=code,
                )
                new_user.is_staff = True
                role = "admin"

            # ...or join as a member of an existing company
            if request.POST.get("company") == "existing_company":
                try:
                    code = request.POST.get("company_code")
                    company = Company.objects.get(code=code)
                except Company.DoesNotExist:
                    messages.error(request, "Incorrect company code!")
                    return render(request, "account/register.html", {"form": form})
                role = "viewer"

            # Data for a person is contained in two models: User and Profile
            new_user.save()
            try:
                latest_employee = Profile.objects.filter(company=company).latest("employee_num")
                employee_num = latest_employee.employee_num + 1
            except Profile.DoesNotExist:
                employee_num = 1

            Profile.objects.create(user=new_user, company=company, role=role, employee_num=employee_num)

            return render(request, "account/register_done.html", {"new_user": new_user})
        return render(request, "account/register.html", {"form": form})


class EditProfileView(LoginRequiredMixin, View):
    """
    View to edit own profile: first name, last name and e-mail address.
    User can not change role or active status himself.

    Access company: company of a request user
    Access roles: all
    """
    def get(self, request):
        user_form = UserEditForm(instance=request.user)
        return render(request, "account/edit.html", {"user_form": user_form})

    def post(self, request):
        user_form = UserEditForm(instance=request.user, data=request.POST)
        if user_form.is_valid():
            user_form.save()
            return redirect(reverse("account:profile_detail",
                                    kwargs={
                                        "company_name": request.user.profile.company.name,
                                        "employee_num": request.user.profile.employee_num
                                    }))
        return render(request, "account/edit.html", {"user_form": user_form})


class ProfileDetailView(LoginRequiredMixin, View):
    """
    View to see the details of a profile.

    Access company: check if company from url is the same as company of request user
    Access roles: all
    """
    def get(self, request, company_name, employee_num):
        company = get_object_or_404(Company, name=company_name)
        if request.user.profile.company != company:
            raise PermissionDenied

        profile = get_object_or_404(Profile, company=company, employee_num=employee_num)
        user = profile.user
        return render(request, "account/profile_detail.html", {"user": user})


class UserListView(LoginRequiredMixin, View):
    """
    See meta information about the company and the list of users.

    Access company: lists data for company of request user
    Access roles: all, but edit links are disabled for non-admins in template
    """

    def get(self, request):
        company = request.user.profile.company
        profiles = Profile.objects.filter(company=company)
        users = [profile.user for profile in profiles]
        return render(request, "account/list_users.html", {"users": users})


class EditUserByAdminView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    View to edit users' data by admin: first name, last name, e-mail address, is active, role.

    The first user (who has is_staff flag) must have is_active=true and role=admin - this can't be changed.
    Otherwise, company could have no admin at all.

    Access company: company_name is in the url and is compared against company of request user
    Access roles: admin only, in test_func()
    """
    def test_func(self):
        return self.request.user.profile.role == "admin"

    def get(self, request, company_name, employee_num):
        company = get_object_or_404(Company, name=company_name)
        profile = get_object_or_404(Profile, employee_num=employee_num)
        user = profile.user
        if request.user.profile.company != company:
            raise PermissionDenied

        user_form = UserEditByAdminForm(instance=user)
        profile_form = ProfileEditByAdminForm(instance=user.profile)
        return render(request, "account/edit_by_admin.html", {"user_form": user_form, "profile_form": profile_form})

    def post(self, request, company_name, employee_num):
        company = get_object_or_404(Company, name=company_name)
        profile = get_object_or_404(Profile, employee_num=employee_num)
        user = profile.user
        if request.user.profile.company != company:
            raise PermissionDenied

        user_form = UserEditByAdminForm(instance=user, data=request.POST)
        profile_form = ProfileEditByAdminForm(instance=user.profile, data=request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            if user.is_staff:
                con1 = user_form.cleaned_data["is_active"] is False
                if con1:
                    user_form.add_error("is_active", "The first user in the company must be active.")
                con2 = profile_form.cleaned_data["role"] != "admin"
                if con2:
                    profile_form.add_error("role", "The first user in the company must be an admin.")
                if con1 or con2:
                    return render(request, "account/edit_by_admin.html",
                                  {"user_form": user_form, "profile_form": profile_form})

            user_form.save()
            profile_form.save()
            return redirect(reverse("account:user_list"))
        return render(request, "account/edit_by_admin.html", {"user_form": user_form, "profile_form": profile_form})
