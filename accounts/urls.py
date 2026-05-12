from django.urls import path
from .views import role_based_login, request_password_reset, verify_otp, set_new_password, resend_otp



app_name = "accounts"

urlpatterns = [
    path("login/", role_based_login, name="login"),
    path("reset-password/", request_password_reset, name="request_password_reset"),
    path("verify-otp/", verify_otp, name="verify_otp"),
    path("new-password/", set_new_password, name="set_new_password"),
    path("resend-otp/", resend_otp, name="resend_otp"),
  


]