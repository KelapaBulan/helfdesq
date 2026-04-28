from django.contrib import admin
from django.urls import path, include
from tiket import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('accounts/login/', views.custom_login, name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/password_reset/',
     auth_views.PasswordResetView.as_view(
         template_name='registration/password_reset.html',
         email_template_name='registration/password_reset_email.html',
         subject_template_name='registration/password_reset_subject.txt',
         success_url='/accounts/password_reset/done/',
     ),
     name='password_reset'),
path('accounts/password_reset/done/',
     auth_views.PasswordResetDoneView.as_view(
         template_name='registration/password_reset_done.html'
     ),
     name='password_reset_done'),
path('accounts/reset/<uidb64>/<token>/',
     auth_views.PasswordResetConfirmView.as_view(
         template_name='registration/password_reset_confirm.html'
     ),
     name='password_reset_confirm'),
path('accounts/reset/done/',
     auth_views.PasswordResetCompleteView.as_view(
         template_name='registration/password_reset_complete.html'
     ),
     name='password_reset_complete'),
    path('admin/', admin.site.urls),

    # App URLs (no prefix)
    path('', include('tiket.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)