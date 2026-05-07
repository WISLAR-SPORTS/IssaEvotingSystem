"""
URL configuration for Evoting project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.contrib import admin
from django.urls import path
from accounts.views import role_based_login,landing_page
from django.urls import path, include
from django.contrib.auth import views as auth_views
from accounts.views import custom_admin_logout
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/logout/', custom_admin_logout, name='logout'),
    path('', landing_page, name='landing'),
    path("", role_based_login, name="home"),
    path("admin/login/", role_based_login, name="home"),
    path('admin/', admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("students/", include("students.urls")),
    path("elections/", include("elections.urls")),
    path("voting/", include("voting.urls")),
    path("admin/login/", role_based_login), 
      #  allauth URLs (Google login, etc.)
    
    path("accounts/", include("allauth.urls")),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)