from django.shortcuts import render, redirect
from django.contrib import messages

from .models import StudentUpload
from .services.student_upload_service import process_student_upload


from django.utils import timezone
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from students.models import StudentRecord
from elections.models import Election  # assuming you have this

from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.shortcuts import render
from elections.models import Election

from django.http import HttpResponseForbidden

@login_required
def student_dashboard(request):
    user = request.user

    # 🔒 ONLY STUDENTS ALLOWED
    if user.role != "student":
        return HttpResponseForbidden("Access denied: Students only")

    student = StudentRecord.objects.filter(user=user).first()

    now = timezone.now()

    active_elections = Election.objects.filter(
        institution=user.institution,
        start_time__lte=now,
        end_time__gte=now
    )

    upcoming_elections = Election.objects.filter(
        institution=user.institution,
        start_time__gt=now
    )

    return render(request, "students/dashboard.html", {
        "student": student,
        "active_elections": active_elections,
        "upcoming_elections": upcoming_elections,
        "user": user,
    })

@login_required
def student_profile(request):
    try:
        student = StudentRecord.objects.get(user=request.user)
    except StudentRecord.DoesNotExist:
        student = None

    return render(request, "students/profile.html", {
        "student": student
        
    })


from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model
from students.models import StudentRecord
from .form import StudentRegistrationForm

User = get_user_model()

def student_register(request):
    if request.method == "POST":
        form = StudentRegistrationForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data["username"].strip().lower()
            student_id = form.cleaned_data["student_id"]
            name = form.cleaned_data["name"]
            password = form.cleaned_data["password"]
            email = form.cleaned_data["email"]
            phone = form.cleaned_data["phone_number"]

            # 🔒 prevent duplicate username
            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already taken")
                return redirect("students:register")

            # 🔒 prevent duplicate phone (SAFE CHECK)
            if hasattr(User, "phone_number"):
                if User.objects.filter(phone_number=phone).exists():
                    messages.error(request, "Phone number already in use")
                    return redirect("students:register")

            # 📌 get student safely
            try:
                student = StudentRecord.objects.get(student_id=student_id)
            except StudentRecord.DoesNotExist:
                messages.error(request, "Invalid student ID")
                return redirect("students:register")

            # 📌 safe branch check (THIS WAS A COMMON CRASH POINT)
            if not student.branch or not hasattr(student.branch, "institution"):
                messages.error(request, "Student branch/institution not assigned")
                return redirect("students:register")

            # 🔍 name validation (safe for None)
            if not student.name or student.name.strip().lower() != name.strip().lower():
                messages.error(request, "Name does not match student record")
                return redirect("students:register")

            # 📌 check if already linked
            if student.user:
                messages.error(request, "Student already registered")
                return redirect("students:register")

            # ✅ create user
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                role="student",
                student_number=student_id,
                phone_number=phone,
                institution=student.branch.institution,
                branch=student.branch,
            )

            # 🔗 link student safely
            user.institution = student.branch.institution
            user.branch = student.branch
            user.save()

            student.user = user
            student.save()

            messages.success(request, "Registration successful. You can now login.")
            return redirect("accounts:login")

        else:
            messages.error(request, "Invalid form data")

    else:
        form = StudentRegistrationForm()

    return render(request, "register.html", {"form": form})