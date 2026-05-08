import pandas as pd
import os
from django.db import transaction
from students.models import StudentRecord, Branch
from institutions.models import Department


def process_student_upload(upload):
    file_path = upload.file.path
    ext = os.path.splitext(file_path)[1].lower()

    # ✅ Support CSV + Excel
    if ext == ".csv":
        df = pd.read_csv(file_path)

    elif ext in [".xlsx", ".xls"]:
        df = pd.read_excel(file_path)

    else:
        raise ValueError("Unsupported file type. Use CSV or Excel.")

    # ✅ Normalize column names (VERY IMPORTANT)
    df.columns = df.columns.str.strip().str.lower()

    required_columns = ["student_id", "name", "branch", "department"]  # Added department

    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Missing column: {col}. Found: {list(df.columns)}")

    errors = []

    with transaction.atomic():
        for index, row in df.iterrows():

            student_id = str(row["student_id"]).strip()
            name = str(row["name"]).strip()
            branch_name = str(row["branch"]).strip()
            department_name = str(row["department"]).strip()  # Added department

            if not student_id or not name or not branch_name or not department_name:
                errors.append(f"Row {index+1}: Missing data")
                continue

            try:
                # Get the branch
                branch = Branch.objects.get(
                    name=branch_name,
                    institution=upload.institution
                )
            except Branch.DoesNotExist:
                errors.append(f"Row {index+1}: Invalid branch '{branch_name}'")
                continue

            try:
                # Get the department
                department = Department.objects.get(
                    name=department_name,
                    branch=branch
                )
            except Department.DoesNotExist:
                errors.append(f"Row {index+1}: Invalid department '{department_name}' for branch '{branch_name}'")
                continue

            # Update or create the StudentRecord
            StudentRecord.objects.update_or_create(
                student_id=student_id,
                defaults={
                    "name": name,
                    "branch": branch,
                    "department": department,  # Added department
                    "institution": upload.institution,
                },
            )

    upload.processed = True
    upload.save()

    return errors