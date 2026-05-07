from django.urls import path
from .views import student_register, student_dashboard, student_profile

app_name = "students"

urlpatterns = [
    path("register/", student_register, name="register"),
    path("dashboard/", student_dashboard, name="dashboard"),
    path("profile/", student_profile, name="student_profile"),

]
