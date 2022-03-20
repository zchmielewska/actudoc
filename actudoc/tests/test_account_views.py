from django.contrib.auth.models import User
from django.test import Client, TestCase

from account.models import Profile
from document.models import Company


class ExtendedTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def create_and_log_viewer(self):
        company = Company.objects.create(name="alpha", full_name="alpha", code="1234")
        user = User.objects.create_user(username="1", email="viewer@example.com", password="pass")
        Profile.objects.create(company=company, user=user, employee_num=1)
        self.client.force_login(user)
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

        data = {
                "email": "example@example.com",
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


class TestLoginView(ExtendedTestCase):
    def test_get(self):
        response = self.client.get("/account/login/")
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post("/account/login/", {"email": "test@test.com", "password": "test"})
        self.assertEqual(response.status_code, 200)

        self.create_and_log_viewer()
        response = self.client.post("/account/login/", {"email": "viewer@example.com", "password": "pass"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/")


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

