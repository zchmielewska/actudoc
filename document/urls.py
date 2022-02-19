from django.urls import path

from document import views

urlpatterns = [
    path('', views.MainView.as_view(), name="main"),
    path('search', views.MainView.as_view(), name="search"),
    path('category/add', views.AddCategoryView.as_view(), name="add_category"),
    path('category/edit/<pk>', views.EditCategoryView.as_view(), name="edit_category"),
    path('category/delete/<pk>', views.DeleteCategoryView.as_view(), name="delete_category"),
    path('product/add', views.AddProductView.as_view(), name="add_product"),
    path('product/edit/<pk>', views.EditProductView.as_view(), name="edit_product"),
    path('product/delete/<pk>', views.DeleteProductView.as_view(), name="delete_product"),
    path('document/add', views.AddDocumentView.as_view(), name="add_document"),
    path('document/edit/<pk>', views.EditDocumentView.as_view(), name="edit_document"),
    path('document/delete/<pk>', views.DeleteDocumentView.as_view(), name="delete_document"),
    path('document/<pk>', views.DocumentDetailView.as_view(), name="document_detail"),
    path('download/<pk>', views.DownloadDocumentView.as_view(), name="download"),
    path('manage', views.ManageView.as_view(), name="manage"),
]