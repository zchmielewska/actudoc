"""actudoc URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from document import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.MainView.as_view(), name="main"),
    path('search', views.MainView.as_view(), name="search"),
    path('document/add', views.AddDocumentView.as_view(), name="add_document"),
    path('product/add', views.AddProductView.as_view(), name="add_product"),
    path('category/add', views.AddCategoryView.as_view(), name="add_category"),
    path('product/edit/<pk>', views.EditProductView.as_view(), name="edit_product"),
    path('category/edit/<pk>', views.EditCategoryView.as_view(), name="edit_category"),
    path('document/edit/<pk>', views.EditDocumentView.as_view(), name="edit_document"),
    path('product/delete/<pk>', views.DeleteProductView.as_view(), name="delete_product"),
    path('category/delete/<pk>', views.DeleteCategoryView.as_view(), name="delete_category"),
    path('document/delete/<pk>', views.DeleteDocumentView.as_view(), name="delete_document"),
    path('document/<pk>', views.DocumentDetailView.as_view(), name="document_detail"),
    path('download/<pk>', views.DownloadDocumentView.as_view(), name="download"),
    path('manage', views.ManageView.as_view(), name="manage"),
    path('register', views.RegisterView.as_view(), name="register"),
    path('login', views.LoginView.as_view(), name="login"),
    path('logout', views.LogoutView.as_view(), name="logout"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
