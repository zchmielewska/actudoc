from django.urls import path

from document import views

urlpatterns = [
    path('', views.MainView.as_view(), name="main"),
    path('search/', views.MainView.as_view(), name="search"),
    path('manage/', views.ManageView.as_view(), name="manage"),

    path('product/add/', views.AddProductView.as_view(), name="add_product"),
    path('product/edit/<company_name>/<company_product_id>', views.EditProductView.as_view(), name="edit_product"),
    path('product/delete/<company_name>/<company_product_id>', views.DeleteProductView.as_view(), name="delete_product"),

    path('category/add', views.AddCategoryView.as_view(), name="add_category"),
    path('category/edit/<company_name>/<company_category_id>', views.EditCategoryView.as_view(), name="edit_category"),
    path('category/delete/<company_name>/<company_category_id>', views.DeleteCategoryView.as_view(), name="delete_category"),

    path('document/add', views.AddDocumentView.as_view(), name="add_document"),
    path('document/edit/<company_name>/<company_document_id>', views.EditDocumentView.as_view(), name="edit_document"),
    path('document/delete/<company_name>/<company_document_id>', views.DeleteDocumentView.as_view(), name="delete_document"),
    path('document/<company_name>/<company_document_id>', views.DocumentDetailView.as_view(), name="document_detail"),
    path('download/<company_name>/<company_document_id>', views.DownloadDocumentView.as_view(), name="download"),
]
