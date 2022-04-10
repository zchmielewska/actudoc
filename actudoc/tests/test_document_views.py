import datetime
import os

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase

from account.models import Profile
from document.models import Category, Company, Document, Product, History


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

    def create_product(self, company):
        product = Product.objects.create(
            company=company,
            company_product_id=1,
            name="Term Life Insurance",
            model="TERM02"
        )
        return product

    def create_category(self, company):
        category = Category.objects.create(
            company=company,
            company_category_id=1,
            name="Technical description"
        )
        return category

    def create_documents(self, user, product, category, n=10):
        for i in range(n):
            Document.objects.create(
                company=user.profile.company,
                company_document_id=i,
                product=product,
                category=category,
                validity_start=f"2022-01-0{i+1}" if i < 9 else f"2022-01-{i+1}",
                file=f"{i}.pdf",
                title="My document",
                created_by=user
            )
        return None


class TestMainView(ExtendedTestCase):
    def test_get(self):
        # Log-in is required
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/account/login?next=/")

        user = self.create_and_log_viewer()
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

        # There is no phrase or documents at the beginning
        self.assertEqual(response.context.get("phrase"), None)
        self.assertEqual(len(response.context.get("documents")), 0)

        # There are 16 documents per page
        product = self.create_product(company=user.profile.company)
        category = self.create_category(company=user.profile.company)
        self.create_documents(user=user, product=product, category=category, n=20)

        response = self.client.get("/")
        self.assertEqual(len(response.context.get("documents")), 16)

        response = self.client.get("/?page=2")
        self.assertEqual(len(response.context.get("documents")), 4)

        response = self.client.get("/?page=2.5")
        self.assertEqual(len(response.context.get("documents")), 16)

        response = self.client.get("/?page=3")
        self.assertEqual(len(response.context.get("documents")), 4)


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

        # List all documents for the given product
        response = self.client.get("/search/?product=1")
        self.assertEqual(len(response.context.get("documents")), 3)

        # List all documents for the given category
        response = self.client.get("/search/?category=1")
        self.assertEqual(len(response.context.get("documents")), 3)


class TestMainViewFix02(ExtendedTestCase):
    fixtures = ["02.json"]

    def test_get(self):
        self.log_user(pk=1)

        # Users sees 16 documents per page (or less at the last page)
        response = self.client.get("/")
        self.assertEqual(len(response.context.get("documents")), 6)


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
        # There are no products at the beginning
        products = Product.objects.all()
        self.assertEqual(products.count(), 0)

    def test_post_by_viewer(self):
        data = {
            "name": "Term Life Insurance",
            "model": "TERM02"
        }

        self.create_and_log_viewer()
        response = self.client.post("/product/add/", data)
        self.assertEqual(response.status_code, 403)

    def test_post_by_contributor(self):
        self.create_and_log_contributor()

        # Create first product
        data1 = {
            "name": "Term Life Insurance",
            "model": "TERM02"
        }
        response = self.client.post("/product/add/", data1)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/manage/")

        products = Product.objects.all()
        self.assertEqual(products.count(), 1)
        self.assertEqual(Product.objects.first().name, "Term Life Insurance")

        response = self.client.get("/manage/")
        products = response.context.get("products")
        self.assertEqual(len(products), 1)

        # Create second product
        data2 = {
            "name": "Annuity",
            "model": "ANN"
        }
        response = self.client.post("/product/add/", data2)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/manage/")

        products = Product.objects.all()
        self.assertEqual(products.count(), 2)
        self.assertEqual(Product.objects.last().name, "Annuity")
        self.assertEqual(Product.objects.last().company_product_id, 2)

        response = self.client.get("/manage/")
        products = response.context.get("products")
        self.assertEqual(len(products), 2)

    def test_post_invalid_data(self):
        data = {
            "model": "TERM02"
        }

        self.create_and_log_contributor()
        response = self.client.post("/product/add/", data)
        products = Product.objects.all()
        self.assertEqual(products.count(), 0)


class TestEditProductViewFix01(ExtendedTestCase):
    fixtures = ["01.json"]

    def test_get(self):
        # Login required
        response = self.client.get("/product/edit/alpha/1")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/account/login?next=/product/edit/alpha/1")

        # Viewers can not edit products
        self.log_user(pk=1)
        response = self.client.get("/product/edit/alpha/1")
        self.assertEqual(response.status_code, 403)

        # Contributors and admins can edit products
        self.log_user(pk=2)
        response = self.client.get("/product/edit/alpha/1")
        self.assertEqual(response.status_code, 200)

        # Only employees can edit products
        self.log_user(pk=3)
        response = self.client.get("/product/edit/alpha/1")
        self.assertEqual(response.status_code, 403)

    def test_post(self):
        data = {
            "name": "Whole Of Life",
            "model": "WOL"
        }

        # Viewers can not edit products
        self.log_user(pk=1)
        response = self.client.post("/product/edit/alpha/1", data)
        self.assertEqual(response.status_code, 403)

        # Contributors and admins can edit products
        user = self.log_user(pk=2)

        products = Product.objects.filter(company=user.profile.company)
        self.assertEqual(products.count(), 1)
        self.assertEqual(products.first().model, "TERM02")

        response = self.client.post("/product/edit/alpha/1", data)
        self.assertEqual(response.url, "/manage/")

        products = Product.objects.filter(company=user.profile.company)
        self.assertEqual(products.count(), 1)
        self.assertEqual(products.first().model, "WOL")

        # Access only for employees
        self.log_user(pk=3)
        response = self.client.post("/product/edit/alpha/1", data)
        self.assertEqual(response.status_code, 403)

    def test_post_invalid_data(self):
        data = {
            "model": "WOL",
        }

        # Contributors and admins can edit products
        user = self.log_user(pk=2)

        # Before edit
        products = Product.objects.filter(company=user.profile.company)
        self.assertEqual(products.count(), 1)
        self.assertEqual(products.first().model, "TERM02")

        response = self.client.post("/product/edit/alpha/1", data)

        # After edit - nothing changed
        products = Product.objects.filter(company=user.profile.company)
        self.assertEqual(products.count(), 1)
        self.assertEqual(products.first().model, "TERM02")


class TestDeleteProductViewFix01(ExtendedTestCase):
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
        # Viewers can not delete products
        self.log_user(pk=1)
        response = self.client.post("/product/delete/alpha/1")
        self.assertEqual(response.status_code, 403)

        # Contributors can delete products
        user = self.log_user(pk=2)
        products = Product.objects.filter(company=user.profile.company)
        self.assertEqual(products.count(), 1)
        self.assertEqual(products.first().model, "TERM02")

        response = self.client.post("/product/delete/alpha/1")
        self.assertEqual(response.url, "/manage/")

        products = Product.objects.filter(company=user.profile.company)
        self.assertEqual(products.count(), 0)

        # Only employees can access
        self.log_user(pk=3)
        response = self.client.post("/product/delete/alpha/1")
        self.assertEqual(response.status_code, 403)


class TestAddCategoryView(ExtendedTestCase):
    def test_get(self):
        # Login required
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
            "file": SimpleUploadedFile("owu.pdf", b"file_content", content_type="application/pdf"),
            "title": "My document",
        }
        response = self.client.post("/document/add/", data)
        self.assertEqual(response.url, "/")

        documents = Document.objects.filter(company=user.profile.company)
        self.assertEqual(documents.count(), 4)
        document = documents.latest("id")
        self.assertEqual(document.product.name, "Term Insurance")
        self.assertEqual(document.file.name, user.profile.company.name + "/" + str(document.company_document_id) + "/" +
                         "owu.pdf")
        document.delete()

    def test_post_add_document_with_duplicated_filename(self):
        open("media/alpha/4/owu.pdf", "x")
        user = self.log_user(pk=2)

        documents = Document.objects.filter(company=user.profile.company)
        self.assertEqual(documents.count(), 3)

        data = {
            "product": "1",
            "category": "1",
            "validity_start": "2022-01-06",
            "file": SimpleUploadedFile("owu.pdf", b"file_content", content_type="application/pdf"),
            "title": "My title",
        }
        self.client.post("/document/add/", data)

        documents = Document.objects.filter(company=user.profile.company)
        self.assertEqual(documents.count(), 4)

        document = Document.objects.latest("id")
        self.assertNotEqual(document.file.name, user.profile.company.name + "/" + str(document.company_document_id) + "/" +
                            "owu.pdf")
        document.delete()
        os.remove("media/alpha/4/owu.pdf")

    def test_post_add_document_with_filename_with_spaces(self):
        user = self.log_user(pk=2)

        documents = Document.objects.filter(company=user.profile.company)
        self.assertEqual(documents.count(), 3)

        data = {
            "product": "1",
            "category": "1",
            "validity_start": "2022-01-06",
            "file": SimpleUploadedFile("o w u.pdf", b"file_content", content_type="application/pdf"),
            "title": "My title",
        }

        self.client.post("/document/add/", data)
        documents = Document.objects.filter(company=user.profile.company)
        self.assertEqual(documents.count(), 4)

        document = Document.objects.latest("id")
        self.assertEqual(document.file.name, user.profile.company.name + "/" + str(document.company_document_id) + "/" +
                         "o_w_u.pdf")
        document.delete()

    def test_post_add_document_with_duplicated_metadata(self):
        user = self.log_user(pk=2)

        documents = Document.objects.filter(company=user.profile.company)
        self.assertEqual(documents.count(), 3)

        data = {
            "product": "1",
            "category": "1",
            "validity_start": "2022-01-01",
            "file": SimpleUploadedFile("file999.pdf", b"file_content", content_type="application/pdf"),
            "title": "My title",
        }

        self.client.post("/document/add/", data)
        documents = Document.objects.filter(company=user.profile.company)
        self.assertEqual(documents.count(), 3)


class TestEditDocumentViewFix03(ExtendedTestCase):
    fixtures = ["03.json"]

    def test_get(self):
        response = self.client.get(f"/document/edit/alpha/1")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/account/login?next=/document/edit/alpha/1")

        self.log_user(pk=1)
        response = self.client.get("/document/edit/alpha/1")
        self.assertEqual(response.status_code, 403)

        self.log_user(pk=2)
        response = self.client.get("/document/edit/alpha/1")
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        user = self.log_user(pk=2)

        documents = Document.objects.filter(company=user.profile.company)
        self.assertEqual(documents.count(), 3)

        document = documents.get(pk=1)
        self.assertEqual(document.product.name, "Term Insurance")
        self.assertEqual(History.objects.count(), 0)

    def test_post_edit_document_change_product(self):
        user = self.log_user(pk=2)
        document = Document.objects.get(pk=1)
        data = {
            "title": document.title,
            "product": "2",
            "category": document.category.id,
            "validity_start": document.validity_start,
            "file": document.file.name
        }
        response = self.client.post("/document/edit/alpha/1", data)
        self.assertEqual(response.url, "/document/alpha/1")

        documents = Document.objects.filter(company=user.profile.company)
        self.assertEqual(documents.count(), 3)
        document = Document.objects.get(pk=1)
        self.assertEqual(document.product.name, "Whole of Life")

        histories = History.objects.all()
        self.assertEqual(histories.count(), 1)
        history = histories.first()
        self.assertEqual(history.document_id, 1)
        self.assertEqual(history.element, "product")
        self.assertEqual(history.changed_from, str(Product.objects.get(pk=1)))
        self.assertEqual(history.changed_to, str(Product.objects.get(pk=2)))
        document.delete()

    def test_post_edit_document_change_category(self):
        user = self.log_user(pk=2)
        documents = Document.objects
        self.assertEqual(documents.count(), 3)

        document = Document.objects.get(pk=2)
        self.assertEqual(document.category.name, "Technical description")

        data = {
            "title": document.title,
            "product": document.product.id,
            "category": "2",
            "validity_start": document.validity_start,
            "file": document.file.name
        }
        response = self.client.post("/document/edit/alpha/2", data)
        self.assertEqual(response.url, "/document/alpha/2")

        documents = Document.objects
        self.assertEqual(documents.count(), 3)

        document = documents.get(pk=2)
        self.assertEqual(document.category.name, "Terms")

        histories = History.objects
        self.assertEqual(histories.count(), 1)
        history = histories.first()
        self.assertEqual(history.document_id, 2)
        self.assertEqual(history.element, "document category")
        self.assertEqual(history.changed_from, "Technical description")
        self.assertEqual(history.changed_to, "Terms")
        document.delete()

    def test_post_edit_without_changes(self):
        user = self.log_user(pk=2)
        document_before_edit = Document.objects.get(pk=1)
        data = {
            "title": document_before_edit.title,
            "product": document_before_edit.product.id,
            "category": document_before_edit.category.id,
            "validity_start": document_before_edit.validity_start,
            "file": document_before_edit.file.name
        }
        response = self.client.post("/document/edit/alpha/1", data)
        self.assertEqual(response.url, "/document/alpha/1")
        document_after_edit = Document.objects.get(pk=1)
        self.assertEqual(document_before_edit, document_after_edit)
        self.assertEqual(History.objects.count(), 0)
        document_after_edit.delete()

    def test_post_edit_document_change_valid_from(self):
        user = self.log_user(pk=2)

        documents = Document.objects
        self.assertEqual(documents.count(), 3)

        document = Document.objects.get(pk=3)
        data = {
            "title": document.title,
            "product": document.product.id,
            "category": document.category.id,
            "validity_start": "1999-12-12",
            "file": document.file.name
        }
        response = self.client.post("/document/edit/alpha/3", data)
        self.assertEqual(response.url, "/document/alpha/3")

        documents = Document.objects
        self.assertEqual(documents.count(), 3)

        document = Document.objects.get(pk=3)
        self.assertEqual(document.validity_start, datetime.date(1999, 12, 12))

        histories = History.objects
        self.assertEqual(histories.count(), 1)
        history = histories.first()
        self.assertEqual(history.document_id, 3)
        self.assertEqual(history.element, "valid from")
        self.assertEqual(history.changed_from, "2022-01-03")
        self.assertEqual(history.changed_to, "1999-12-12")
        document.delete()


class TestDeleteDocumentViewFix01(ExtendedTestCase):
    fixtures = ["01.json"]

    def test_get(self):
        response = self.client.get("/document/delete/alpha/1")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/account/login?next=/document/delete/alpha/1")

        self.log_user(pk=1)
        response = self.client.get("/document/delete/alpha/1")
        self.assertEqual(response.status_code, 403)

        self.log_user(pk=2)
        response = self.client.get("/document/delete/alpha/1")
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        user = self.log_user(pk=2)
        self.assertEqual(Document.objects.filter(company=user.profile.company).count(), 3)
        response = self.client.post("/document/delete/alpha/1")
        self.assertEqual(response.url, "/")
        self.assertEqual(Document.objects.filter(company=user.profile.company).count(), 2)


class TestDocumentDetailViewFix01(ExtendedTestCase):
    fixtures = ["01.json"]

    def test_get(self):
        response = self.client.get("/document/alpha/1")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/account/login?next=/document/alpha/1")

        self.log_user(pk=1)
        response = self.client.get("/document/alpha/1")
        self.assertEqual(response.status_code, 200)


class TestDownloadDocumentViewFix01(ExtendedTestCase):
    fixtures = ["01.json"]

    def test_get(self):
        response = self.client.get("/download/alpha/1")
        self.assertEqual(response.status_code, 302)

        user = self.log_user(pk=1)
        open("media/alpha/fileA.pdf", "x")
        response = self.client.get("/download/alpha/1")
        self.assertEqual(response.status_code, 200)
        os.remove("media/alpha/fileA.pdf")
