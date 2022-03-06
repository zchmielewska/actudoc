from django.urls import path
from django.contrib.auth import views as auth_views

from account import views


app_name = 'account'

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('password-change/', auth_views.PasswordChangeView.as_view(), name='password_change'),
    path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'),
    path('password-reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('edit/', views.EditProfileView.as_view(), name='profile_edit'),
    path('edit/<pk>/', views.EditUserByAdminView.as_view(), name='user_edit_by_admin'),
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('<username>/', views.ProfileDetailView.as_view(), name='profile_detail'),
]

