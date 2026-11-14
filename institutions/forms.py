from django import forms
from django.contrib.auth import get_user_model
from django.db import transaction

from institutions.models import Institution

User = get_user_model()


class InstitutionRegistrationForm(forms.Form):
    institution_name = forms.CharField(max_length=255)
    institution_email = forms.EmailField()
    contact_phone = forms.CharField(max_length=30)
    logo = forms.ImageField(required=False)

    admin_username = forms.CharField(max_length=150)
    admin_email = forms.EmailField()
    admin_phone = forms.CharField(max_length=20)
    password = forms.CharField(
        widget=forms.PasswordInput
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput
    )

    def clean_institution_name(self):
        name = self.cleaned_data["institution_name"].strip()

        if Institution.objects.filter(name__iexact=name).exists():
            raise forms.ValidationError(
                "An institution with this name already exists."
            )

        return name

    def clean_admin_username(self):
        username = self.cleaned_data["admin_username"]

        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError(
                "This username is already taken."
            )

        return username

    def clean_admin_email(self):
        email = self.cleaned_data["admin_email"].strip()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "This email is already registered."
            )

        return email

    def clean_admin_phone(self):
        phone = self.cleaned_data["admin_phone"].strip()

        if User.objects.filter(phone_number=phone).exists():
            raise forms.ValidationError(
                "This phone number is already registered."
            )

        return phone

    def clean(self):
        cleaned_data = super().clean()

        if (
            cleaned_data.get("password")
            and cleaned_data.get("confirm_password")
            and cleaned_data["password"]
            != cleaned_data["confirm_password"]
        ):
            self.add_error(
                "confirm_password",
                "Passwords do not match.",
            )

        return cleaned_data

    @transaction.atomic
    def save(self):
        data = self.cleaned_data

        institution = Institution.objects.create(
            name=data["institution_name"],
            email=data["institution_email"],
            contact_phone=data["contact_phone"],
            logo=data.get("logo"),
            status="pending",
        )

        admin = User(
            username=data["admin_username"],
            email=data["admin_email"],
            phone_number=data["admin_phone"],
            role="institution_admin",
            institution=institution,
            is_active=False,
        )
        admin.set_password(data["password"])
        admin.save()

        return institution, admin