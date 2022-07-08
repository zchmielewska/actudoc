from django.contrib import auth
from django.contrib.auth.models import User
from django.test import Client, TestCase

from account.models import Profile
from document.models import Company


class ExtendedTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def create_viewer(self):
        company = Company.objects.create(name="alpha", full_name="alpha", code="1234")
        user = User.objects.create_user(username="1", email="viewer@example.com", password="pass")
        Profile.objects.create(company=company, user=user, employee_num=1)
        return user

    def create_and_log_viewer(self):
        user = self.create_viewer()
        self.client.force_login(user)
        return user

    def create_inactive_user(self):
        company = Company.objects.create(name="alpha", full_name="alpha", code="1234")
        user = User.objects.create_user(username="1", email="viewer@example.com", password="pass", is_active=False)
        Profile.objects.create(company=company, user=user, employee_num=1)
        return user

    def log_user(self, pk):
        user = User.objects.get(pk=pk)
        self.client.force_login(user)
        return user


class TestRegisterView(ExtendedTestCase):
    def test_get(self):
        response = self.client.get("/account/register/")
        self.assertEqual(response.status_code, 200)

    def test_post_register_new_company(self):
        self.assertEqual(Company.objects.count(), 0)
        self.assertEqual(User.objects.count(), 0)

        data = {
            "email": "example@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "password": "HJk&ui34",
            "password2": "HJk&ui34",
            "company": "new_company",
            "company_short_name": "gamma",
            "company_full_name": "Gamme Insurance Group",
        }

        response = self.client.post("/account/register/", data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Company.objects.count(), 1)
        self.assertEqual(User.objects.count(), 1)


class TestRegisterViewFix04(ExtendedTestCase):
    fixtures = ["04.json"]

    def test_post_register_existing_company(self):
        self.assertEqual(Company.objects.count(), 1)
        self.assertEqual(User.objects.count(), 0)

        # First employee
        data = {
                "email": "johndoe@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "password": "HJk&ui34",
                "password2": "HJk&ui34",
                "company": "existing_company",
                "company_code": "1234",
            }

        response = self.client.post("/account/register/", data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Company.objects.count(), 1)
        self.assertEqual(User.objects.count(), 1)

        # Second employee
        data = {
                "email": "marypoppins@example.com",
                "first_name": "Mary",
                "last_name": "Poppins",
                "password": "Er&w89ty",
                "password2": "Er&w89ty",
                "company": "existing_company",
                "company_code": "1234",
            }

        response = self.client.post("/account/register/", data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Company.objects.count(), 1)
        self.assertEqual(User.objects.count(), 2)


class TestLoginView(ExtendedTestCase):
    def test_get(self):
        response = self.client.get("/account/login/")
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        self.create_viewer()

        self.client.post("/account/login/", {"email": "viewer@example.com", "password": "pass"})
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

    def test_post_incorrect_credentials(self):
        self.create_viewer()

        # Incorrect password
        self.client.post("/account/login/", {"email": "viewer@example.com", "password": "wrong"})
        user = auth.get_user(self.client)
        self.assertFalse(user.is_authenticated)

        # Incorrect username
        self.client.post("/account/login/", {"email": "wrong@wrong.com", "password": "pass"})
        user = auth.get_user(self.client)
        self.assertFalse(user.is_authenticated)

    def test_post_inactive_user(self):
        self.create_inactive_user()

        self.client.post("/account/login/", {"email": "viewer@example.com", "password": "pass"})
        user = auth.get_user(self.client)
        self.assertFalse(user.is_authenticated)


class TestProfileDetailViewFix01(ExtendedTestCase):
    fixtures = ["01.json"]

    def test_get(self):
        response = self.client.get("/account/alpha/1/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/account/login?next=/account/alpha/1/")

        self.log_user(pk=3)
        response = self.client.get("/account/alpha/1/")
        self.assertEqual(response.status_code, 403)

        self.log_user(pk=1)
        response = self.client.get("/account/alpha/1/")
        self.assertEqual(response.status_code, 200)


class TestEditProfileViewFix01(ExtendedTestCase):
    fixtures = ["01.json"]

    def test_get(self):
        response = self.client.get("/account/edit/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/account/login?next=/account/edit/")

        self.log_user(pk=1)
        response = self.client.get("/account/edit/")
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        user = self.log_user(pk=1)
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "johndoe@example.com"
        }
        response = self.client.post("/account/edit/", data)
        self.assertEqual(response.url, "/account/alpha/1/")
        user = self.log_user(pk=1)
        self.assertEqual(user.first_name, "John")


class TestUserListViewFix01(ExtendedTestCase):
    fixtures = ["01.json"]

    def test_get(self):
        response = self.client.get("/account/users/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/account/login?next=/account/users/")

        self.log_user(pk=1)
        response = self.client.get("/account/users/")
        self.assertEqual(response.status_code, 200)


class TestEditUserByAdminViewFix05(ExtendedTestCase):
    fixtures = ["05.json"]

    def test_get(self):
        response = self.client.get("/account/edit/alpha/2/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/account/login?next=/account/edit/alpha/2/")

        self.log_user(pk=2)
        response = self.client.get("/account/edit/alpha/2/")
        self.assertEqual(response.status_code, 403)

        self.log_user(pk=1)
        response = self.client.get("/account/edit/alpha/2/")
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "johndoe@example.com",
            "active": True,
            "role": "viewer",
        }

        self.log_user(pk=2)
        response = self.client.post("/account/edit/alpha/2/", data)
        self.assertEqual(response.status_code, 403)

        self.log_user(pk=1)
        response = self.client.post("/account/edit/alpha/2/", data)
        self.assertEqual(response.url, "/account/users/")

        edited_user = User.objects.get(pk=2)
        self.assertEqual(edited_user.first_name, "John")
