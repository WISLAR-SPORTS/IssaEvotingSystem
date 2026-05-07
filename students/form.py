from django import forms


from django import forms
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django import forms
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from .models import User

class StudentRegistrationForm(forms.Form):
    username = forms.CharField(max_length=150)
    student_id = forms.CharField(max_length=100)
    name = forms.CharField(max_length=255)

    email = forms.EmailField(required=True)

    phone_number = forms.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^\+?256\d{9}$|^0\d{9}$',
                message="Enter a valid Ugandan phone number"
            )
        ]
    )

    password = forms.CharField(
        widget=forms.PasswordInput,
        min_length=6
    )
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    # 🔒 normalize + sanitize
    def clean_username(self):
        username = self.cleaned_data["username"].strip()

        if User.objects.filter(username=username).exists():
            raise ValidationError("Username already taken")

        return username

    def clean_student_id(self):
        return self.cleaned_data["student_id"].strip()

    def clean_name(self):
        return self.cleaned_data["name"].strip()

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def clean_phone_number(self):
        phone = self.cleaned_data["phone_number"].strip()

        # normalize to +256 format
        if phone.startswith("0"):
            phone = "+256" + phone[1:]

        if User.objects.filter(phone_number=phone).exists():
            raise ValidationError("Phone number already in use")

        return phone

    # 🔐 password confirmation + extra validation
    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password")
        p2 = cleaned_data.get("confirm_password")

        if p1 and p2:
            if p1 != p2:
                raise ValidationError("Passwords do not match")

            if len(p1) < 6:
                raise ValidationError("Password must be at least 6 characters long")

        return cleaned_data