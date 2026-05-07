from django.core.mail import send_mail
import random


def generate_otp():
    return str(random.randint(100000, 999999))


def send_otp_email(email, code):
    send_mail(
        subject="Password Reset OTP",
        message=f"Your OTP is {code}. It expires in 10 minutes.",
        from_email=None,
        recipient_list=[email]
    )