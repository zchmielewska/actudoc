import mimetypes
import os
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, UpdateView, DeleteView

from document import models
from document import forms
from document.utils import utils


class MainView(LoginRequiredMixin, View):
    """
    Home page of the application.

    Shows ten newest documents in reverse-chronological order of company's documents.
    Allows searching documents using a phrase.

    Access company: filtering of objects
    Access users: all
    """
    def get(self, request):
        company = request.user.profile.company
        phrase = request.GET.get("phrase")
        if phrase:
            documents = utils.search(phrase, company)
        else:
            documents = models.Document.objects.filter(company=company).order_by("-id")[:10]

        ctx = {
            "documents": documents,
            "phrase": phrase,
            "no_documents": documents.count(),
        }
        return render(request, "document/main.html", ctx)


class ManageView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Manage products and categories of the company. Add, edit or delete objects.

    Access company: filtering of objects
    Access users: contributors and admins (test_func)
    """
    def test_func(self):
        return utils.user_is_contributor_or_admin(self.request)

    def get(self, request):
        company = self.request.user.profile.company
        categories = models.Category.objects.filter(company=company).order_by("id")
        products = models.Product.objects.filter(company=company).order_by("id")
        return render(request, "document/manage.html", {"categories": categories, "products": products})


class AddProductView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Form to add a new product.

    Access company: posted form will take company info from user
    Access users: contributors and admins (test_func)
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
            company_product_id = models.Product.objects.filter(company=company).count() + 1
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
    Access users: contributores and admins (test_func)
    """
    def test_func(self):
        return utils.user_is_contributor_or_admin(self.request)

    def instance(self, company_name, company_product_id):
        company = get_object_or_404(models.Company, name=company_name)
        product = get_object_or_404(models.Product, company=company, company_product_id=company_product_id)
        return product

    def get(self, request, company_name, company_product_id):
        if request.user.profile.company.name != company_name:
            raise PermissionDenied

        product = self.instance(company_name, company_product_id)
        form = forms.ProductForm(instance=product)
        return render(request, "document/product_update_form.html", {"form": form})

    def post(self, request, company_name, company_product_id):
        if request.user.profile.company.name != company_name:
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
    Access users: contributores and admins (test_func)
    """
    def test_func(self):
        return utils.user_is_contributor_or_admin(self.request)

    def instance(self, company_name, company_product_id):
        company = get_object_or_404(models.Company, name=company_name)
        product = get_object_or_404(models.Product, company=company, company_product_id=company_product_id)
        return product

    def get(self, request, company_name, company_product_id):
        if request.user.profile.company.name != company_name:
            raise PermissionDenied

        product = self.instance(company_name, company_product_id)
        return render(request, "document/product_confirm_delete.html", {"product": product})

    def post(self, request, company_name, company_product_id):
        if request.user.profile.company.name != company_name:
            raise PermissionDenied

        product = self.instance(company_name, company_product_id)
        product.delete()
        messages.success(request, "Insurance product deleted!")
        return redirect(reverse_lazy("manage"))


class AddCategoryView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Form to add a new category.

    Access company: posted form will take company info from user
    Access users: contributores and admins (test_func)
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
            company_category_id = models.Category.objects.filter(company=company).count() + 1
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
    Access users: contributores and admins (test_func)
    """
    def test_func(self):
        return utils.user_is_contributor_or_admin(self.request)

    def instance(self, company_name, company_category_id):
        company = get_object_or_404(models.Company, name=company_name)
        category = get_object_or_404(models.Category, company=company, company_category_id=company_category_id)
        return category

    def get(self, request, company_name, company_category_id):
        if request.user.profile.company.name != company_name:
            raise PermissionDenied

        category = self.instance(company_name, company_category_id)
        form = forms.CategoryForm(instance=category)
        return render(request, "document/category_update_form.html", {"form": form})

    def post(self, request, company_name, company_category_id):
        if request.user.profile.company.name != company_name:
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
    Access users: contributores and admins (test_func)
    """
    def test_func(self):
        return utils.user_is_contributor_or_admin(self.request)

    def instance(self, company_name, company_category_id):
        company = get_object_or_404(models.Company, name=company_name)
        category = get_object_or_404(models.Category, company=company, company_category_id=company_category_id)
        return category

    def get(self, request, company_name, company_category_id):
        if request.user.profile.company.name != company_name:
            raise PermissionDenied

        category = self.instance(company_name, company_category_id)
        return render(request, "document/category_confirm_delete.html", {"category": category})

    def post(self, request, company_name, company_category_id):
        if request.user.profile.company.name != company_name:
            raise PermissionDenied

        category = self.instance(company_name, company_category_id)
        category.delete()
        messages.success(request, "Document category deleted!")
        return redirect(reverse_lazy("manage"))


class AddDocumentView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Add a new document.

    User chooses products and categories only from the ones available in their company.

    Access company: posted form will take company info from user
    Access users: contributores and admins (test_func)
    """
    def test_func(self):
        return utils.user_is_contributor_or_admin(self.request)

    def get(self, request):
        form = forms.DocumentForm()
        form.fields["product"].queryset = models.Product.objects.filter(company=request.user.profile.company)
        form.fields["category"].queryset = models.Category.objects.filter(company=request.user.profile.company)
        return render(request, "document/document_form.html", {"form": form})

    def post(self, request):
        form = forms.DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            cd = form.cleaned_data
            form_file = cd.get("file")
            document = models.Document.objects.create(
                company=request.user.profile.company,
                company_document_id=models.Document.objects.filter(company=request.user.profile.company).count() + 1,
                product=cd.get("product"),
                category=cd.get("category"),
                validity_start=cd.get("validity_start"),
                file=form_file,
                created_by=request.user,
            )
            #TODO
            if document.file != form_file:
                text = utils.get_filename_msg(document, sent_filename=form_file.name)
                messages.info(request, text)

            messages.success(request, "Document added!")
            return redirect("main")
        else:
            form.fields["product"].queryset = models.Product.objects.filter(company=request.user.profile.company)
            form.fields["category"].queryset = models.Category.objects.filter(company=request.user.profile.company)
            return render(request, "document/document_form.html", {"form": form})


class EditDocumentView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Edit an existing document and save history of the changes made to the document.
    """
    # model = models.Document
    # template_name_suffix = "_update_form"
    # form_class = forms.DocumentForm

    def test_func(self):
        return utils.user_is_contributor_or_admin(self.request)

    def get(self, request, company_name, company_document_id):
        company = get_object_or_404(models.Company, name=company_name)
        document = get_object_or_404(models.Document, company=company, company_document_id=company_document_id)
        form = forms.DocumentForm(instance=document)
        form.fields["product"].queryset = models.Product.objects.filter(company=request.user.profile.company)
        form.fields["category"].queryset = models.Category.objects.filter(company=request.user.profile.company)
        return render(request, "document/document_update_form.html", {"form": form})

    # def get_initial(self):
    #     initial = super(EditDocumentView, self).get_initial()
    #     initial["validity_start"] = self.object.validity_start.strftime("%Y-%m-%d")
    #     return initial

    def post(self, request, company_name, company_document_id):
        form = forms.DocumentForm(request.POST, request.FILES)

        if form.is_valid():
            # Form contains the filename delivered by the user
            form_file = form.cleaned_data.get("file")

            # Filename after saving might differ from the one uploaded
            document_new = form.save(commit=False)
            document_old = models.Document.objects.get(id=self.object.id)

            # Filename is converted to None after deletion
            data_old = document_old.__dict__.copy()
            if self.request.FILES.get("file"):
                document_old.file.delete()

            # History of changes gets saved
            document_new.save()
            data_new = document_new.__dict__.copy()
            utils.save_history(data_old, data_new, user=self.request.user)

            messages.success(self.request, "Document updated!")

            # Other documents might use the file with the same name
            if document_new.file != form_file:
                text = utils.get_filename_msg(document_new, sent_filename=form_file.name)
                messages.info(self.request, text)

            return redirect("document_detail", document_new.id)
        else:
            print("invalid form")
            form.fields["product"].queryset = models.Product.objects.filter(company=request.user.profile.company)
            form.fields["category"].queryset = models.Category.objects.filter(company=request.user.profile.company)
            return render(request, "document/document_update_form.html", {"form": form})


# class EditDocumentView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
#     """
#     Edit an existing document and save history of the changes made to the document.
#     """
#     model = models.Document
#     template_name_suffix = "_update_form"
#     form_class = forms.DocumentForm
#
#     def test_func(self):
#         # utils.user_is_contributor_or_admin(self.request)
#         return self.request.user.groups.filter(name="manager").exists()
#
#     def get_initial(self):
#         initial = super(EditDocumentView, self).get_initial()
#         initial["validity_start"] = self.object.validity_start.strftime("%Y-%m-%d")
#         return initial
#
#     def form_valid(self, form):
#         # Form contains the filename delivered by the user
#         form_file = form.cleaned_data.get("file")
#
#         # Filename after saving might differ from the one uploaded
#         document_new = form.save(commit=False)
#         document_old = models.Document.objects.get(id=self.object.id)
#
#         # Filename is converted to None after deletion
#         data_old = document_old.__dict__.copy()
#         if self.request.FILES.get("file"):
#             document_old.file.delete()
#
#         # History of changes gets saved
#         document_new.save()
#         data_new = document_new.__dict__.copy()
#         utils.save_history(data_old, data_new, user=self.request.user)
#
#         messages.success(self.request, "Document updated!")
#
#         # Other documents might use the file with the same name
#         if document_new.file != form_file:
#             text = utils.get_filename_msg(document_new, sent_filename=form_file.name)
#             messages.info(self.request, text)
#
#         return redirect("document_detail", document_new.id)


class DeleteDocumentView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete a document."""
    model = models.Document
    success_url = reverse_lazy("main")
    success_message = "Document deleted!"

    def test_func(self):
        return self.request.user.groups.filter(name="manager").exists()


class DocumentDetailView(LoginRequiredMixin, View):
    """Show document's details."""
    # def get(self, request, pk):
    def get(self, request, company_name, company_document_id):
        company = get_object_or_404(models.Company, name=company_name)
        if company != request.user.profile.company:
            raise Http404

        document = get_object_or_404(models.Document, company=company, company_document_id=company_document_id)
        history_set = document.history_set.all().order_by("-changed_at")
        ctx = {
            "document": document,
            "history_set": history_set,
        }
        return render(request, "document/document_detail.html", ctx)


class DownloadDocumentView(LoginRequiredMixin, View):
    """Download a document's file."""
    def get(self, request, pk):
        document = get_object_or_404(models.Document, id=pk)
        filepath = os.path.join(settings.MEDIA_ROOT, document.file.name)
        if os.path.exists(filepath):
            with open(filepath, "rb") as fh:
                mime_type, _ = mimetypes.guess_type(filepath)
                response = HttpResponse(fh.read(), content_type=mime_type)
                response["Content-Disposition"] = "inline; filename=" + os.path.basename(filepath)
                return response
        else:
            raise Http404

