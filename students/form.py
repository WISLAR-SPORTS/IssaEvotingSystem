from django import forms
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from accounts.models import User
from students.models import StudentRecord


class StudentRegistrationForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"placeholder": "Username"}),
    )
    student_id = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"placeholder": "Student ID"}),
    )
    name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={"placeholder": "Full Name"}),
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"placeholder": "Email Address"}),
    )
    phone_number = forms.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^\+?256\d{9}$|^0\d{9}$',
                message="Enter a valid Ugandan phone number",
            )
        ],
        widget=forms.TextInput(attrs={"placeholder": "Phone Number"}),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Password"}),
        min_length=6,
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Confirm Password"})
    )

    # 🔒 Normalize and sanitize username
    def clean_username(self):
        username = self.cleaned_data["username"].strip().lower()

        if User.objects.filter(username=username).exists():
            raise ValidationError("Username already taken")

        return username

    # 🔒 Validate student ID
    def clean_student_id(self):
        student_id = self.cleaned_data["student_id"].strip()

        # Ensure the student ID exists in the database
        if not StudentRecord.objects.filter(student_id=student_id).exists():
            raise ValidationError("Invalid student ID")

        return student_id

    # 🔒 Validate name
    def clean_name(self):
        name = self.cleaned_data["name"].strip()

        # Ensure the name matches the student record
        student_id = self.cleaned_data.get("student_id")
        if student_id:
            try:
                student = StudentRecord.objects.get(student_id=student_id)
                if student.name.strip().lower() != name.lower():
                    raise ValidationError("Name does not match the student record")
            except StudentRecord.DoesNotExist:
                pass

        return name

    # 🔒 Normalize and validate email
    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(email=email).exists():
            raise ValidationError("Email already in use")

        return email

    # 🔒 Normalize and validate phone number
    def clean_phone_number(self):
        phone = self.cleaned_data["phone_number"].strip()

        # Normalize to +256 format
        if phone.startswith("0"):
            phone = "+256" + phone[1:]

        if User.objects.filter(phone_number=phone).exists():
            raise ValidationError("Phone number already in use")

        return phone

    # 🔐 Password confirmation and validation
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password:
            if password != confirm_password:
                raise ValidationError("Passwords do not match")

            if len(password) < 6:
                raise ValidationError("Password must be at least 6 characters long")

            # Ensure password contains at least one number and one letter
            if not any(char.isdigit() for char in password):
                raise ValidationError("Password must contain at least one number")

            if not any(char.isalpha() for char in password):
                raise ValidationError("Password must contain at least one letter")

        return cleaned_data