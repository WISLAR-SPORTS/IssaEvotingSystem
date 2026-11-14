from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login

from django.contrib.sessions.models import Session
from .models import User
from django.utils import timezone
from .models import PasswordResetOTP
from .utils import generate_otp, send_otp_email 




from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.sessions.models import Session
from django.shortcuts import render, redirect
from django.utils import timezone

from django.http import JsonResponse
from django.db import connection

def database_status(request):
    try:
        connection.ensure_connection()

        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()

        return JsonResponse({
            "database": connection.vendor,
            "connected": connection.is_usable(),
            "query_test": result[0] == 1,
            "status": "SUCCESS"
        })

    except Exception as e:
        return JsonResponse({
            "connected": False,
            "status": "FAILED",
            "error": str(e)
        }, status=500)


def role_based_login(request):
    if request.method == "POST":
        identifier = request.POST.get("identifier", "").strip()
        password = request.POST.get("password", "")
        remember_me = request.POST.get("remember_me")

        # Find user by username or email
        user_obj = User.objects.filter(
            username__iexact=identifier
        ).first()

        if not user_obj:
            user_obj = User.objects.filter(
                email__iexact=identifier
            ).first()

        if not user_obj:
            messages.error(request, "Invalid username or password")
            return render(request, "accounts/login.html")

        # Authenticate
        user = authenticate(
            request,
            username=user_obj.username,
            password=password
        )

        if user is None:
            messages.error(request, "Invalid username or password")
            return render(request, "accounts/login.html")

        # Single device login check
        if user.current_session_key:
            session = Session.objects.filter(
                session_key=user.current_session_key
            ).first()

            if session and session.expire_date > timezone.now():
                messages.error(
                    request,
                    "You are already logged in on another device."
                )
                return redirect("accounts:login")

            user.current_session_key = None
            user.save(update_fields=["current_session_key"])

        # Login user
        login(request, user)

     

        # Save session key
        request.session.save()
        user.current_session_key = request.session.session_key
        user.save(update_fields=["current_session_key"])

        # Superuser first
        if user.is_superuser:
            return redirect("/admin/")

        # Check role
        if not user.role:
            messages.error(request, "User role not assigned.")
            return redirect("accounts:login")

        if user.role in [
            "super_admin",
            "institution_admin",
            "branch_admin"
        ]:
            return redirect("/admin/")

        if user.role == "student":
            return redirect("students:dashboard")

        messages.error(request, "Invalid user role.")
        return redirect("accounts:login")

    return render(request, "accounts/login.html")


def custom_admin_logout(request):
    if request.user.is_authenticated:
        request.user.current_session_key = None
        request.user.save()

    # 🔥 fully destroy session
    request.session.flush()

    logout(request)
    return redirect('landing')


def landing_page(request):
    return render(request, "home.html")


from django.contrib.auth.models import User

import json
import threading
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth import get_user_model

User = get_user_model()


def send_email_async(email, code):
    try:
        send_otp_email(email, code)
    except Exception as e:
        print("EMAIL ERROR:", str(e))


def request_password_reset(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email = data.get("email")
        except:
            return JsonResponse({"success": False, "error": "Invalid request"})

        user = User.objects.filter(email=email).first()
        if not user:
            return JsonResponse({"success": False, "error": "Email not found"})

        code = generate_otp()
        PasswordResetOTP.objects.create(user=user, code=code)

        request.session["reset_email"] = email

        # 🔥 FIX: send email in background (prevents timeout)
        threading.Thread(
            target=send_email_async,
            args=(user.email, code)
        ).start()

        return JsonResponse({"success": True})

    return render(request, "accounts/request_otp.html")


def verify_otp(request):
    email = request.session.get("reset_email")

    if not email:
        return JsonResponse({"success": False, "error": "Session expired"})

    user = User.objects.filter(email=email).first()
    if not user:
        return JsonResponse({"success": False, "error": "User not found"})

    if request.method == "POST":
        try:
            data = json.loads(request.body)
            code = data.get("code")
        except:
            return JsonResponse({"success": False, "error": "Invalid request"})

        otp = PasswordResetOTP.objects.filter(
            user=user,
            code=code,
            is_used=False
        ).first()

        if otp and not otp.is_expired():
            otp.is_used = True
            otp.save()

            request.session["reset_user_id"] = user.id

            return JsonResponse({"success": True})

        return JsonResponse({"success": False, "error": "Invalid or expired code"})

    return JsonResponse({"success": False, "error": "Invalid request"})

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
import json

User = get_user_model()


def set_new_password(request):
    user_id = request.session.get("reset_user_id")

    if not user_id:
        return redirect("accounts:request_password_reset")

    if request.method == "GET":
        return render(request, "accounts/new_password.html")

    if request.method == "POST":
        try:
            data = json.loads(request.body)
            password = data.get("password")
        except:
            return JsonResponse({"success": False, "error": "Invalid request"})

        if not password or len(password) < 6:
            return JsonResponse({"success": False, "error": "Password too short"})

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({"success": False, "error": "User not found"})

        user.password = make_password(password)
        user.save()

        request.session.flush()

        return JsonResponse({"success": True})

        
from .models import PasswordResetOTP
from django.contrib.auth import get_user_model

User = get_user_model()

def resend_otp(request):
    email = request.session.get("reset_email")

    if not email:
        return redirect("accounts:request_password_reset")

    user = User.objects.filter(email=email).first()
    if not user:
        return redirect("accounts:request_password_reset")

    # Optional: invalidate old OTPs
    PasswordResetOTP.objects.filter(user=user, is_used=False).update(is_used=True)

    # generate new OTP
    code = generate_otp()
    PasswordResetOTP.objects.create(user=user, code=code)

    send_otp_email(user.email, code)

    return render(request, "accounts/verify_otp.html", {
        "message": "A new OTP has been sent."
    })
from django.http import HttpResponseNotAllowed

def health_check(request):
    if request.method not in ["GET", "HEAD"]:
        return HttpResponseNotAllowed(["GET", "HEAD"])
    
    return JsonResponse({"status": "ok"})

from django.shortcuts import redirect


from django.contrib import messages
from django.shortcuts import render, redirect

from .forms import InstitutionRegistrationForm


def institution_register(request):
    if request.method == "POST":
        form = InstitutionRegistrationForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Registration submitted successfully. "
                "Your institution is awaiting superadmin "
                "verification. You can log in after approval.",
            )
            return redirect("accounts:login")
    else:
        form = InstitutionRegistrationForm()

    return render(
        request,
        "institutionregister.html",
        {"form": form},
    )