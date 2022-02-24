import mimetypes
import os
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
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

    Shows ten newest documents in reverse-chronological order.
    Allows searching documents using a phrase.
    """
    def get(self, request):
        phrase = request.GET.get("phrase")
        if phrase:
            documents = utils.search(phrase)
        else:
            documents = models.Document.objects.order_by("-id")[:10]

        ctx = {
            "documents": documents,
            "phrase": phrase,
            "no_documents": documents.count(),
        }
        return render(request, "document/main.html", ctx)


class ManageView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Manage products and categories. Add, edit or delete objects."""
    def test_func(self):
        return self.request.user.groups.filter(name="manager").exists()

    def get(self, request):
        categories = models.Category.objects.all().order_by("id")
        products = models.Product.objects.all().order_by("id")
        return render(request, "document/manage.html", {"categories": categories, "products": products})


class AddProductView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, CreateView):
    """Form to add a new product."""
    def test_func(self):
        return self.request.user.groups.filter(name="manager").exists()

    model = models.Product
    fields = "__all__"
    success_url = reverse_lazy("manage")
    success_message = "Insurance product added!"


class EditProductView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    """Form to edit an existing product."""
    def test_func(self):
        return self.request.user.groups.filter(name="manager").exists()

    model = models.Product
    fields = "__all__"
    template_name_suffix = "_update_form"
    success_url = reverse_lazy("manage")
    success_message = "Insurance product updated!"


class DeleteProductView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, DeleteView):
    """Delete a product."""
    model = models.Product
    success_url = reverse_lazy("manage")
    success_message = "Insurance product deleted!"

    def test_func(self):
        return self.request.user.groups.filter(name="manager").exists()

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super(DeleteProductView, self).delete(request, *args, **kwargs)


class AddCategoryView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, CreateView):
    """Form to add a new category."""
    model = models.Category
    fields = "__all__"
    success_url = reverse_lazy("manage")
    success_message = "Document category added!"

    def test_func(self):
        return self.request.user.groups.filter(name="manager").exists()


class EditCategoryView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    """Form to edit an existing category."""
    model = models.Category
    fields = "__all__"
    template_name_suffix = "_update_form"
    success_url = reverse_lazy("manage")
    success_message = "Document category updated!"

    def test_func(self):
        return self.request.user.groups.filter(name="manager").exists()


class DeleteCategoryView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, DeleteView):
    """Delete a category."""
    model = models.Category
    success_url = reverse_lazy("manage")
    success_message = "Document category deleted!"

    def test_func(self):
        return self.request.user.groups.filter(name="manager").exists()

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super(DeleteCategoryView, self).delete(request, *args, **kwargs)


class AddDocumentView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Add a new document.
    """
    def test_func(self):
        return self.request.user.groups.filter(name="manager").exists()

    def get(self, request):
        form = forms.DocumentForm
        return render(request, "document/document_form.html", {"form": form})

    def post(self, request):
        form = forms.DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.cleaned_data.get("product")
            category = form.cleaned_data.get("category")
            validity_start = form.cleaned_data.get("validity_start")
            form_file = form.cleaned_data.get("file")

            document = models.Document.objects.create(
                product=product,
                category=category,
                validity_start=validity_start,
                file=form_file,
                created_by=request.user,
            )
            if document.file != form_file:
                text = utils.get_filename_msg(document, sent_filename=form_file.name)
                messages.info(request, text)

            messages.success(request, "Document added!")
            return redirect("main")

        return render(request, "document/document_form.html", {"form": form})


class EditDocumentView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Edit an existing document and save history of the changes made to the document.
    """
    model = models.Document
    template_name_suffix = "_update_form"
    form_class = forms.DocumentForm

    def test_func(self):
        return self.request.user.groups.filter(name="manager").exists()

    def get_initial(self):
        initial = super(EditDocumentView, self).get_initial()
        initial["validity_start"] = self.object.validity_start.strftime("%Y-%m-%d")
        return initial

    def form_valid(self, form):
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


class DeleteDocumentView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete a document."""
    model = models.Document
    success_url = reverse_lazy("main")
    success_message = "Document deleted!"

    def test_func(self):
        return self.request.user.groups.filter(name="manager").exists()


class DocumentDetailView(LoginRequiredMixin, View):
    """Show document's details."""
    def get(self, request, pk):
        document = get_object_or_404(models.Document, pk=pk)
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


# class RegisterView(View):
#     """Form to create a new account."""
#     def get(self, request):
#         form = forms.RegisterForm()
#         return render(request, "register.html", {"form": form})
#
#     def post(self, request):
#         form = forms.RegisterForm(request.POST)
#         if form.is_valid():
#             username = form.cleaned_data["username"]
#             password = form.cleaned_data["password"]
#             password2 = form.cleaned_data["password2"]
#
#             username_is_taken = username in User.objects.values_list("username", flat=True)
#             if username_is_taken:
#                 form.add_error("username", "This username has already been taken.")
#                 return render(request, "register.html", {"form": form})
#
#             passwords_are_different = password != password2
#             if passwords_are_different:
#                 form.add_error("username", "Passwords are different.")
#                 return render(request, "register.html", {"form": form})
#
#             user = User.objects.create_user(username=username, email=None, password=password)
#             login(request, user)
#             return redirect("main")
#         else:
#             return render(request, "register.html", {"form": form})
#

# class LoginView(View):
#     """Form to log in."""
#     def get(self, request):
#         form = forms.LoginForm()
#         return render(request, "login.html", {"form": form})
#
#     def post(self, request):
#         form = forms.LoginForm(request.POST)
#         if form.is_valid():
#             username = form.cleaned_data["username"]
#             password = form.cleaned_data["password"]
#             user = authenticate(username=username, password=password)
#
#             if user is not None:
#                 login(request, user)
#                 url_next = request.GET.get("next", "/")
#                 return redirect(url_next)
#             else:
#                 form.add_error("username", "Incorrect username or password.")
#         return render(request, "login.html", {"form": form})
#
#
# class LogoutView(View):
#     """Form to log out."""
#     def get(self, request):
#         logout(request)
#         return redirect("main")
