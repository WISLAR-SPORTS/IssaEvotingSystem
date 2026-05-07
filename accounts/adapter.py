from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from django.shortcuts import redirect
from django.contrib.auth import get_user_model
from django.contrib import messages

User = get_user_model()


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):

    def pre_social_login(self, request, sociallogin):

        email = sociallogin.user.email  # ✅ FIX HERE

        if not email:
            messages.error(request, "Google did not return an email.")
            raise ImmediateHttpResponse(redirect("accounts:login"))

        email = email.strip().lower()

        # 🔍 check if email exists in your DB
        if not User.objects.filter(email__iexact=email).exists():

            messages.error(request, "This email is not registered in the system.")
            raise ImmediateHttpResponse(redirect("accounts:login"))

        # 🔗 link social account
        user = User.objects.get(email__iexact=email)
        sociallogin.connect(request, user)