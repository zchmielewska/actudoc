import os
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import Http404, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View

from document import models
from document import forms
from document.utils import utils


class MainView(LoginRequiredMixin, View):
    """
    Home page of the application.

    Shows ten newest documents in reverse-chronological order of company's documents.
    Allows searching documents using a phrase.

    Access company: filtering of objects based on request user's company
    Access roles: all
    """
    def get(self, request):
        company = request.user.profile.company
        documents = models.Document.objects.filter(company=company)

        # User can search documents with a phrase
        phrase = request.GET.get("phrase")
        if phrase:
            documents = utils.search(phrase, company)

        # User can search documents by product
        company_product_id = request.GET.get("product")
        product = None
        if company_product_id:
            product = get_object_or_404(models.Product, company=company, company_product_id=company_product_id)
            documents = documents.filter(product=product)

        # User can search documents by category
        company_category_id = request.GET.get("category")
        category = None
        if company_category_id:
            category = get_object_or_404(models.Category, company=company, company_category_id=company_category_id)
            documents = documents.filter(category=category)

        # Documents are split by pages
        paginator = Paginator(documents, 16)
        page = request.GET.get("page")

        try:
            documents = paginator.page(page)
        except PageNotAnInteger:
            documents = paginator.page(1)
        except EmptyPage:
            documents = paginator.page(paginator.num_pages)

        ctx = {
            "page": page,
            "documents": documents,
            "phrase": phrase,
            "product": product,
            "category": category,
        }
        return render(request, "document/main.html", ctx)


class ManageView(LoginRequiredMixin, View):
    """
    Manage products and categories of the company. Add, edit or delete objects.

    Access company: filtering of objects
    Access role: all can access but only contributors and admins have active links to edit/delete
    """
    def get(self, request):
        company = self.request.user.profile.company
        categories = models.Category.objects.filter(company=company)
        products = models.Product.objects.filter(company=company)
        return render(request, "document/manage.html", {"categories": categories, "products": products})


class AddProductView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Form to add a new product.

    Products have internal ids within company (company_product_id).

    Access company: posted form will take company info from user
    Access roles: contributors and admins (test_func)
    """
    def test_func(self):
        return utils.user_is_contributor_or_admin(self.request)

    def get(self, request):
        form = forms.ProductForm
        return render(request, "document/product_form.html", {"form": form})

    def post(self, request):
        form = forms.ProductForm(request.POST)
        if form.is_valid():
            company = request.user.profile.company
            try:
                latest_product = models.Product.objects.filter(company=company).latest("company_product_id")
                company_product_id = latest_product.company_product_id + 1
            except models.Product.DoesNotExist:
                company_product_id = 1

            name = form.cleaned_data["name"]
            model = form.cleaned_data["model"]
            models.Product.objects.create(
                company=company,
                company_product_id=company_product_id,
                name=name,
                model=model,
            )
            messages.success(request, "Insurance product added!")
            return redirect(reverse_lazy("manage"))
        else:
            return render(request, "document/product_form.html", {"form": form})


class EditProductView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, View):
    """
    Form to edit an existing product.

    Access company: url + logged in user (get + post)
    Access roles: contributors and admins (test_func)
    """
    def test_func(self):
        return utils.user_is_contributor_or_admin(self.request)

    def instance(self, company_name, company_product_id):
        company = get_object_or_404(models.Company, name=company_name)
        product = get_object_or_404(models.Product, company=company, company_product_id=company_product_id)
        return product

    def get(self, request, company_name, company_product_id):
        if not utils.user_is_employee(request, company_name):
            raise PermissionDenied

        product = self.instance(company_name, company_product_id)
        form = forms.ProductForm(instance=product)
        return render(request, "document/product_update_form.html", {"form": form})

    def post(self, request, company_name, company_product_id):
        if not utils.user_is_employee(request, company_name):
            raise PermissionDenied

        product = self.instance(company_name, company_product_id)
        form = forms.ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Insurance product updated!")
            return redirect(reverse_lazy("manage"))
        else:
            return render(request, "document/product_update_form.html", {"form": form})


class DeleteProductView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Delete a product.

    Access company: url + logged in user (get + post)
    Access roles: contributors and admins (test_func)
    """
    def test_func(self):
        return utils.user_is_contributor_or_admin(self.request)

    def instance(self, company_name, company_product_id):
        company = get_object_or_404(models.Company, name=company_name)
        product = get_object_or_404(models.Product, company=company, company_product_id=company_product_id)
        return product

    def get(self, request, company_name, company_product_id):
        if not utils.user_is_employee(request, company_name):
            raise PermissionDenied

        product = self.instance(company_name, company_product_id)
        return render(request, "document/product_confirm_delete.html", {"product": product})

    def post(self, request, company_name, company_product_id):
        if not utils.user_is_employee(request, company_name):
            raise PermissionDenied

        product = self.instance(company_name, company_product_id)
        product.delete()
        messages.success(request, "Insurance product deleted!")
        return redirect(reverse_lazy("manage"))


class AddCategoryView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Form to add a new category.

    Access company: posted form will take company info from request user
    Access roles: contributors and admins (test_func)
    """
    def test_func(self):
        return utils.user_is_contributor_or_admin(self.request)

    def get(self, request):
        form = forms.CategoryForm
        return render(request, "document/category_form.html", {"form": form})

    def post(self, request):
        form = forms.CategoryForm(request.POST)
        if form.is_valid():
            company = request.user.profile.company

            try:
                latest_category = models.Category.objects.filter(company=company).latest("company_category_id")
                company_category_id = latest_category.company_category_id + 1
            except models.Category.DoesNotExist:
                company_category_id = 1

            name = form.cleaned_data["name"]
            models.Category.objects.create(
                company=company,
                company_category_id=company_category_id,
                name=name,
            )
            messages.success(request, "Document category added!")
            return redirect(reverse_lazy("manage"))
        else:
            return render(request, "document/category_form.html", {"form": form})


class EditCategoryView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Form to edit an existing category.

    Access company: url + logged in user (get + post)
    Access roles: contributors and admins (test_func)
    """
    def test_func(self):
        return utils.user_is_contributor_or_admin(self.request)

    def instance(self, company_name, company_category_id):
        company = get_object_or_404(models.Company, name=company_name)
        category = get_object_or_404(models.Category, company=company, company_category_id=company_category_id)
        return category

    def get(self, request, company_name, company_category_id):
        if not utils.user_is_employee(request, company_name):
            raise PermissionDenied

        category = self.instance(company_name, company_category_id)
        form = forms.CategoryForm(instance=category)
        return render(request, "document/category_update_form.html", {"form": form})

    def post(self, request, company_name, company_category_id):
        if not utils.user_is_employee(request, company_name):
            raise PermissionDenied

        category = self.instance(company_name, company_category_id)
        form = forms.CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Document category updated!")
            return redirect(reverse_lazy("manage"))
        else:
            return render(request, "document/category_update_form.html", {"form": form})


class DeleteCategoryView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Delete a category.

    Access company: url + logged in user (get + post)
    Access roles: contributors and admins (test_func)
    """
    def test_func(self):
        return utils.user_is_contributor_or_admin(self.request)

    def instance(self, company_name, company_category_id):
        company = get_object_or_404(models.Company, name=company_name)
        category = get_object_or_404(models.Category, company=company, company_category_id=company_category_id)
        return category

    def get(self, request, company_name, company_category_id):
        if not utils.user_is_employee(request, company_name):
            raise PermissionDenied

        category = self.instance(company_name, company_category_id)
        return render(request, "document/category_confirm_delete.html", {"category": category})

    def post(self, request, company_name, company_category_id):
        if not utils.user_is_employee(request, company_name):
            raise PermissionDenied

        category = self.instance(company_name, company_category_id)
        category.delete()
        messages.success(request, "Document category deleted!")
        return redirect(reverse_lazy("manage"))


class AddDocumentView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Add a new document.

    User chooses products and categories only from the ones available in their company.
    Document has an internal id within the company (company_document_id).
    Two documents can't have the same product, category and validity start date.

    Access company: posted form will take company info from request user
    Access roles: contributors and admins (test_func)
    """
    def test_func(self):
        return utils.user_is_contributor_or_admin(self.request)

    def get(self, request):
        form = forms.DocumentAddForm()
        company = request.user.profile.company
        form.fields["product"].queryset = models.Product.objects.filter(company=company)
        form.fields["category"].queryset = models.Category.objects.filter(company=company)
        return render(request, "document/document_form.html", {"form": form})

    def post(self, request):
        form = forms.DocumentAddForm(request.POST, request.FILES)
        company = request.user.profile.company
        if form.is_valid():
            document = form.save(commit=False)
            cd = form.cleaned_data
            form_file = cd.get("file")

            # Documents have internal id within the company
            try:
                latest_document = models.Document.objects.filter(company=company).latest("company_document_id")
                company_document_id = latest_document.company_document_id + 1
            except models.Document.DoesNotExist:
                company_document_id = 1

            # Document has some attributes outside the form
            document.company = company
            document.company_document_id = company_document_id
            document.file = form_file
            document.created_by = request.user
            document.save()
            form.save_m2m()

            # Saved filename might be different from the sent filename
            saved_filename = os.path.basename(document.file.name)
            sent_filename = form_file.name
            if saved_filename != sent_filename:
                text = utils.get_filename_msg(saved_filename=saved_filename, sent_filename=sent_filename,
                                              company_name=company.name)
                messages.info(request, text)

            messages.success(request, "Document added!")
            return redirect("main")
        else:
            form.fields["product"].queryset = models.Product.objects.filter(company=company)
            form.fields["category"].queryset = models.Category.objects.filter(company=company)
            return render(request, "document/document_form.html", {"form": form})


class EditDocumentView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Edit an existing document and save history of the changes made to the document.
    It's not allowed to change file itself. The user should add a new document and delete the existing one.

    Access company: company name is in url and then check in get() and post()
    Access roles: contributors and admins (test_func)
    """
    def instance(self, company_name, company_document_id):
        company = get_object_or_404(models.Company, name=company_name)
        document = get_object_or_404(models.Document, company=company, company_document_id=company_document_id)
        return document

    def test_func(self):
        return utils.user_is_contributor_or_admin(self.request)

    def get(self, request, company_name, company_document_id):
        if not utils.user_is_employee(request, company_name):
            raise PermissionDenied

        document = self.instance(company_name, company_document_id)
        form = forms.DocumentEditForm(instance=document)
        company = request.user.profile.company
        form.fields["product"].queryset = models.Product.objects.filter(company=company)
        form.fields["category"].queryset = models.Category.objects.filter(company=company)
        return render(request, "document/document_update_form.html", {"form": form})

    def post(self, request, company_name, company_document_id):
        if not utils.user_is_employee(request, company_name):
            raise PermissionDenied

        company = request.user.profile.company
        document = self.instance(company_name, company_document_id)
        form = forms.DocumentEditForm(request.POST, request.FILES, instance=document)

        if form.is_valid():
            document = form.save()
            messages.success(self.request, "Document updated!")
            return redirect("document_detail", document.company.name, document.company_document_id)
        else:
            form.fields["product"].queryset = models.Product.objects.filter(company=company)
            form.fields["category"].queryset = models.Category.objects.filter(company=company)
            return render(request, "document/document_update_form.html", {"form": form})


class DeleteDocumentView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, View):
    """
    Delete a document.

    Access company: company name is in url and then check in get() and post()
    Access roles: contributors and admins (test_func)
    """
    def instance(self, company_name, company_document_id):
        company = get_object_or_404(models.Company, name=company_name)
        document = get_object_or_404(models.Document, company=company, company_document_id=company_document_id)
        return document

    def test_func(self):
        return utils.user_is_contributor_or_admin(self.request)

    def get(self, request, company_name, company_document_id):
        if not utils.user_is_employee(request, company_name):
            raise PermissionDenied

        document = self.instance(company_name, company_document_id)
        return render(request, "document/document_confirm_delete.html", {"document": document})

    def post(self, request, company_name, company_document_id):
        if not utils.user_is_employee(request, company_name):
            raise PermissionDenied

        document = self.instance(company_name, company_document_id)
        document.delete()
        messages.success(request, "Document deleted!")
        return redirect(reverse_lazy("main"))


class DocumentDetailView(LoginRequiredMixin, View):
    """
    Show document's details.

    Access company: company name is in url and then check in get()
    Access roles: all
    """
    def get(self, request, company_name, company_document_id):
        if not utils.user_is_employee(request, company_name):
            raise PermissionDenied

        company = get_object_or_404(models.Company, name=company_name)
        document = get_object_or_404(models.Document, company=company, company_document_id=company_document_id)
        history_set = document.history_set.all().order_by("-changed_at")
        ctx = {
            "document": document,
            "document_filename": os.path.basename(document.file.name),
            "history_set": history_set,
        }
        return render(request, "document/document_detail.html", ctx)


class DownloadDocumentView(LoginRequiredMixin, View):
    """
    Download a document's file.

    Access company: company name is in url and then check in get()
    Access roles: all
    """
    def get(self, request, company_name, company_document_id):
        if not utils.user_is_employee(request, company_name):
            raise PermissionDenied

        company = get_object_or_404(models.Company, name=company_name)
        document = get_object_or_404(models.Document, company=company, company_document_id=company_document_id)

        filepath = os.path.join(settings.MEDIA_ROOT, document.file.name)
        if os.path.exists(filepath):
            with open(filepath, "rb") as fh:
                mime_type = "application/pdf"
                response = HttpResponse(fh.read(), content_type=mime_type)
                response["Content-Disposition"] = "inline; filename=" + os.path.basename(filepath)
                return response
        else:
            raise Http404
