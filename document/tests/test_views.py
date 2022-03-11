from django.contrib.auth.models import User
from django.test import Client, TestCase

from account.models import Profile
from  document.models import Company


class ExtendedTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def log_viewer(self):
        company = Company.objects.create(name="alpha", full_name="Alphabetical Insurance Company", code="1234")
        user = User.objects.create(username="1", email="viewer@example.com")
        Profile.objects.create(company=company, user=user, employee_num=1)
        self.client.force_login(user)


class TestMainView(ExtendedTestCase):
    def test_get(self):
        # Log-in is required
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/account/login?next=/")

        self.log_viewer()
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

