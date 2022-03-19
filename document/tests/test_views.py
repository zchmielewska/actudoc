from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase

from account.models import Profile
from document.forms import DocumentAddForm
from document.models import Category, Company, Document, Product


class ExtendedTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def create_and_log_viewer(self):
        company = Company.objects.create(name="alpha", full_name="alpha", code="1234")
        user = User.objects.create(username="1", email="viewer@example.com")
        Profile.objects.create(company=company, user=user, employee_num=1)
        self.client.force_login(user)
        return user

    def create_and_log_contributor(self):
        company = Company.objects.create(name="beta", full_name="beta", code="5678")
        user = User.objects.create(username="2", email="contributor@example.com")
        Profile.objects.create(company=company, user=user, employee_num=1, role="contributor")
        self.client.force_login(user)
        return user

    def log_user(self, pk):
        user = User.objects.get(pk=pk)
        self.client.force_login(user)
        return user


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

        # Contributors and admins can add products
        self.create_and_log_contributor()
        response = self.client.get("/product/add/")
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        self.create_and_log_contributor()
        response = self.client.get("/product/add/")
        self.assertEqual(response.status_code, 200)

        num_products = Product.objects.count()
        self.assertEqual(num_products, 0)

        response = self.client.get("/manage/")
        products = response.context.get("products")
        self.assertEqual(len(products), 0)

        data = {
            "name": "Term Life Insurance",
            "model": "TERM02"
        }
        response = self.client.post("/product/add/", data)
        self.assertEqual(response.url, "/manage/")

        num_products = Product.objects.count()
        self.assertEqual(num_products, 1)
        self.assertEqual(Product.objects.first().name, "Term Life Insurance")

        response = self.client.get("/manage/")
        products = response.context.get("products")
        self.assertEqual(len(products), 1)


class TestEditProductViewFix01(ExtendedTestCase):
    fixtures = ["01.json"]

    def test_get(self):
        response = self.client.get("/product/edit/alpha/1")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/account/login?next=/product/edit/alpha/1")

        # Viewers can't edit products
        self.log_user(pk=1)
        response = self.client.get("/product/edit/alpha/1")
        self.assertEqual(response.status_code, 403)

        # Contributors and admins can edit products
        self.log_user(pk=2)
        response = self.client.get("/product/edit/alpha/1")
        self.assertEqual(response.status_code, 200)

        # Access only for employees
        self.log_user(pk=3)
        response = self.client.get("/product/edit/alpha/1")
        self.assertEqual(response.status_code, 403)

    def test_post(self):
        # Contributors and admins can edit products
        user = self.log_user(pk=2)

        products = Product.objects.filter(company=user.profile.company)
        self.assertEqual(products.count(), 1)
        self.assertEqual(products.first().model, "TERM02")

        data = {
            "name": "Whole Of Life",
            "model": "WOL"
        }
        response = self.client.post("/product/edit/alpha/1", data)
        self.assertEqual(response.url, "/manage/")

        products = Product.objects.filter(company=user.profile.company)
        self.assertEqual(products.count(), 1)
        self.assertEqual(products.first().model, "WOL")


class TestDeleteProductView01(ExtendedTestCase):
    fixtures = ["01.json"]

    def test_get(self):
        response = self.client.get("/product/delete/alpha/1")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/account/login?next=/product/delete/alpha/1")

        # Viewers can't delete products
        self.log_user(pk=1)
        response = self.client.get("/product/delete/alpha/1")
        self.assertEqual(response.status_code, 403)

        # Contributors and admins can edit products
        self.log_user(pk=2)
        response = self.client.get("/product/delete/alpha/1")
        self.assertEqual(response.status_code, 200)

        # Access only for employees
        self.log_user(pk=3)
        response = self.client.get("/product/delete/alpha/1")
        self.assertEqual(response.status_code, 403)

    def test_post(self):
        user = self.log_user(pk=2)
        products = Product.objects.filter(company=user.profile.company)
        self.assertEqual(products.count(), 1)
        self.assertEqual(products.first().model, "TERM02")

        response = self.client.post("/product/delete/alpha/1")
        self.assertEqual(response.url, "/manage/")

        products = Product.objects.filter(company=user.profile.company)
        self.assertEqual(products.count(), 0)


class TestAddCategoryView(ExtendedTestCase):
    def test_get(self):
        response = self.client.get("/category/add/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/account/login?next=/category/add/")

        # It's forbidden for viewers to add categories
        self.create_and_log_viewer()
        response = self.client.get("/category/add/")
        self.assertEqual(response.status_code, 403)

        # Contributors and admins can add categories
        self.create_and_log_contributor()
        response = self.client.get("/category/add/")
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        self.create_and_log_contributor()
        categories = Category.objects
        self.assertEqual(categories.count(), 0)

        response = self.client.post("/category/add/", {"name": "Terms"})
        self.assertEqual(response.url, "/manage/")

        categories = Category.objects
        self.assertEqual(categories.count(), 1)
        self.assertEqual(Category.objects.first().name, "Terms")


class TestEditCategoryViewFix01(ExtendedTestCase):
    fixtures = ["01.json"]

    def test_get(self):
        response = self.client.get("/category/edit/alpha/1")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/account/login?next=/category/edit/alpha/1")

        # Viewers can't edit categories
        self.log_user(pk=1)
        response = self.client.get("/category/edit/alpha/1")
        self.assertEqual(response.status_code, 403)

        # Contributors and admins can edit categories
        self.log_user(pk=2)
        response = self.client.get("/category/edit/alpha/1")
        self.assertEqual(response.status_code, 200)

        # Access only for employees
        self.log_user(pk=3)
        response = self.client.get("/category/edit/alpha/1")
        self.assertEqual(response.status_code, 403)

    def test_post(self):
        user = self.log_user(pk=2)
        categories = Category.objects.filter(company=user.profile.company)
        self.assertEqual(categories.count(), 1)
        self.assertEqual(categories.first().name, "Technical description")

        data = {
            "name": "Test report"
        }
        response = self.client.post("/category/edit/alpha/1", data)
        self.assertEqual(response.url, "/manage/")

        categories = Category.objects.filter(company=user.profile.company)
        self.assertEqual(categories.count(), 1)
        self.assertEqual(categories.first().name, "Test report")


class TestDeleteCategoryViewFix01(ExtendedTestCase):
    fixtures = ["01.json"]

    def test_get(self):
        response = self.client.get("/category/delete/alpha/1")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/account/login?next=/category/delete/alpha/1")

        # Viewers can't delete categories
        self.log_user(pk=1)
        response = self.client.get("/category/delete/alpha/1")
        self.assertEqual(response.status_code, 403)

        # Contributors and admins can edit categories
        self.log_user(pk=2)
        response = self.client.get("/category/delete/alpha/1")
        self.assertEqual(response.status_code, 200)

        # Access only for employees
        self.log_user(pk=3)
        response = self.client.get("/category/delete/alpha/1")
        self.assertEqual(response.status_code, 403)

    def test_post(self):
        user = self.log_user(pk=2)

        categories = Category.objects.filter(company=user.profile.company)
        self.assertEqual(categories.count(), 1)

        response = self.client.post("/category/delete/alpha/1")
        self.assertEqual(response.url, "/manage/")

        categories = Category.objects.filter(company=user.profile.company)
        self.assertEqual(categories.count(), 0)


class TestAddDocumentViewFix01(ExtendedTestCase):
    fixtures = ["01.json"]

    def test_get(self):
        response = self.client.get("/document/add/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/account/login?next=/document/add/")

        # Viewer can't add document
        self.log_user(pk=1)
        response = self.client.get("/document/add/")
        self.assertEqual(response.status_code, 403)

        # Contributor and admin can add document
        self.log_user(pk=2)
        response = self.client.get("/document/add/")
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        user = self.log_user(pk=2)
        documents = Document.objects.filter(company=user.profile.company)
        self.assertEqual(documents.count(), 3)

        data = {
            "product": "1",
            "category": "1",
            "validity_start": "2022-01-06",
            "file": SimpleUploadedFile("alpha/owu.pdf", b"file_content", content_type="pdf")
        }
        response = self.client.post("/document/add/", data)
        form = DocumentAddForm(data=data)
        print("form.is_valid(): ", form.is_valid())
        print("form.errors ", form.errors)

        # self.assertEqual(response.url, "/")
        documents = Document.objects.filter(company=user.profile.company)
        # self.assertEqual(documents.count(), 4)
        self.assertEqual(response, "")

    #     document = documents.last()
    #     self.assertEqual(document.product.name, "Produkt testowy")
    #     self.assertEqual(document.file.name, "owu.pdf")
    #     document.delete()
    #
    # def test_post_add_document_with_duplicated_filename(self):
    #     open("media/file1.pdf", "x")
    #     self.log_manager()
    #     self.assertEqual(models.Document.objects.count(), 5)
    #     data = {
    #         "product": "1",
    #         "category": "1",
    #         "validity_start": "2022-01-06",
    #         "file": SimpleUploadedFile("file1.pdf", b"file_content", content_type="pdf")
    #     }
    #     self.client.post("/document/add", data)
    #     self.assertEqual(models.Document.objects.count(), 6)
    #     document = models.Document.objects.last()
    #     self.assertNotEqual(document.file.name, "file1.pdf")
    #     document.delete()
    #     os.remove("media/file1.pdf")
    #
    # def test_post_add_document_with_filename_with_spaces(self):
    #     self.log_manager()
    #     self.assertEqual(models.Document.objects.count(), 5)
    #     data = {
    #         "product": "1",
    #         "category": "1",
    #         "validity_start": "2022-01-06",
    #         "file": SimpleUploadedFile("file 1.pdf", b"file_content", content_type="pdf")
    #     }
    #     self.client.post("/document/add", data)
    #     self.assertEqual(models.Document.objects.count(), 6)
    #     document = models.Document.objects.last()
    #     self.assertEqual(document.file.name, "file_1.pdf")
    #     document.delete()
    #
    # def test_post_add_document_with_duplicated_metadata(self):
    #     self.log_manager()
    #     self.assertEqual(models.Document.objects.count(), 5)
    #     data = {
    #         "product": "1",
    #         "category": "1",
    #         "validity_start": "2022-01-01",
    #         "file": SimpleUploadedFile("file999.pdf", b"file_content", content_type="pdf")
    #     }
    #     self.client.post("/document/add", data)
    #     self.assertEqual(models.Document.objects.count(), 5)
