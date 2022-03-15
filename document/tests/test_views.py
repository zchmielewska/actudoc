from django.contrib.auth.models import User
from django.test import Client, TestCase

from account.models import Profile
from document.models import Company, Document


class ExtendedTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def create_and_log_viewer(self):
        company = Company.objects.create(name="test", full_name="test", code="1234")
        user = User.objects.create(username="1", email="viewer@example.com")
        Profile.objects.create(company=company, user=user, employee_num=1)
        self.client.force_login(user)

    def log_user(self, pk):
        user = User.objects.get(pk=pk)
        self.client.force_login(user)


class TestMainView(ExtendedTestCase):
    def test_get(self):
        # Log-in is required
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/account/login?next=/")

        self.create_and_log_viewer()
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

        # There is no phrase or documents
        self.assertEqual(response.context.get("phrase"), None)
        self.assertEqual(len(response.context.get("documents")), 0)


class TestMainViewFix01(ExtendedTestCase):
    fixtures = ["01.json"]

    def test_get(self):
        self.log_user(pk=1)

        # Users sees only documents of their's company
        response = self.client.get("/")
        self.assertEqual(len(response.context.get("documents")), 3)

        # Documents are presented starting with the newest (using pagination)
        self.assertEqual(response.context.get("documents").object_list[0].id, 3)

        # User can search for documents with a phrase, searching in various places, for example...
        response = self.client.get("/search/?phrase=fileA")
        self.assertEqual(response.context.get("phrase"), "fileA")
        self.assertEqual(len(response.context.get("documents")), 1)
        self.assertEqual(response.context.get("documents").object_list[0].id, 1)

        # ...company document id with a hash (#n)
        response = self.client.get("/search/?phrase=%233")
        self.assertEqual(response.context.get("phrase"), "#3")
        self.assertEqual(len(response.context.get("documents")), 1)
        self.assertEqual(response.context.get("documents").object_list[0].id, 3)

        # ...product
        response = self.client.get("/search/?phrase=term+insurance")
        self.assertEqual(response.context.get("phrase"), "term insurance")
        self.assertEqual(len(response.context.get("documents")), 3)

        # ...category
        response = self.client.get("/search/?phrase=technical+description")
        self.assertEqual(response.context.get("phrase"), "technical description")
        self.assertEqual(len(response.context.get("documents")), 3)

        response = self.client.get("/search/?phrase=non+existing")
        self.assertEqual(response.context.get("phrase"), "non existing")
        self.assertEqual(len(response.context.get("documents")), 0)


class TestMainViewFix02(ExtendedTestCase):
    fixtures = ["02.json"]

    def test_get(self):
        self.log_user(pk=1)

        # Users sees 5 documents per page (or less at the last page)
        response = self.client.get("/")
        self.assertEqual(len(response.context.get("documents")), 5)

        response = self.client.get("/?page=2")
        self.assertEqual(len(response.context.get("documents")), 1)


class TestManageView(ExtendedTestCase):
    def test_get(self):
        # Log-in is required
        response = self.client.get("/manage/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/account/login?next=/manage/")

        self.create_and_log_viewer()
        response = self.client.get("/manage/")
        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context.get("products")), 0)
        self.assertEqual(len(response.context.get("categories")), 0)


class TestManageViewFix01(ExtendedTestCase):
    fixtures = ["01.json"]

    def test_get(self):
        self.log_user(pk=1)

        response = self.client.get("/manage/")
        self.assertEqual(len(response.context.get("products")), 1)
        self.assertEqual(len(response.context.get("categories")), 1)


class TestAddProductView(ExtendedTestCase):
    def test_get(self):
        response = self.client.get("/product/add/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/account/login?next=/product/add/")

        # It's forbidden for viewers to add products
        self.create_and_log_viewer()
        response = self.client.get("/product/add/")
        self.assertEqual(response.status_code, 403)

