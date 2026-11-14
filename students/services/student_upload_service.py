
import os
import pandas as pd

from django.db import transaction
from students.models import StudentRecord, Branch
from institutions.models import Department


def process_student_upload(upload):
    file_path = upload.file.path
    ext = os.path.splitext(file_path)[1].lower()

    required_columns = [
        "student_id",
        "name",
        "branch",
        "department",
    ]

    errors = []

    try:
        # 1. Read the file without assuming the first row is the header.
        if ext == ".csv":
            df = pd.read_csv(
                file_path,
                dtype=str,
                header=None,
                encoding="utf-8-sig",
                keep_default_na=False,
            )
        elif ext in (".xlsx", ".xls"):
            df = pd.read_excel(
                file_path,
                dtype=str,
                header=None,
                keep_default_na=False,
            )
        else:
            raise ValueError(
                "Unsupported file type. Upload a CSV or Excel file."
            )

        if df.empty:
            raise ValueError("The uploaded file is empty.")

        # 2. Find the header row, even if there are title/blank rows.
        header_index = None

        def normalize(value):
            return (
                str(value)
                .strip()
                .lower()
                .replace("\ufeff", "")
                .replace(" ", "_")
                .replace("-", "_")
            )

        for index, row in df.iterrows():
            values = [normalize(value) for value in row.tolist()]

            if all(column in values for column in required_columns):
                header_index = index
                break

        if header_index is None:
            # Fallback for files with no header row but exactly four columns.
            # Assumes the column order is student_id, name, branch, department.
            if len(df.columns) == 4:
                first_row = [
                    normalize(value)
                    for value in df.iloc[0].tolist()
                ]

                known_headers = {
                    "student_id", "name", "branch", "department",
                    "unnamed: 0", "unnamed: 1",
                    "unnamed: 2", "unnamed: 3",
                }

                if all(value in known_headers for value in first_row):
                    header_index = 0
                    df.columns = required_columns
                    df = df.iloc[1:].reset_index(drop=True)
                else:
                    df.columns = required_columns
            else:
                raise ValueError(
                    "Could not identify the student file columns. "
                    f"Expected: {required_columns}. "
                    f"Found {len(df.columns)} columns. "
                    "Please upload a file with the four required columns."
                )

            if header_index is None:
                pass
        else:
            # Apply the detected header and discard rows above it.
            df.columns = [
                normalize(value)
                for value in df.iloc[header_index].tolist()
            ]
            df = df.iloc[header_index + 1:].reset_index(drop=True)

        # 3. Validate required columns.
        df.columns = [normalize(column) for column in df.columns]

        # Remove duplicate or irrelevant columns by selecting required ones.
        missing = [
            column for column in required_columns
            if column not in df.columns
        ]

        if missing:
            raise ValueError(
                f"Missing columns: {missing}. "
                f"Found columns: {list(df.columns)}"
            )

        df = df[required_columns].fillna("")

        # 4. Process records atomically.
        # A database failure rolls back student changes.
        with transaction.atomic():
            for row_number, (_, row) in enumerate(
                df.iterrows(),
                start=header_index + 2 if header_index is not None else 2,
            ):
                student_id = str(row["student_id"]).strip()
                name = str(row["name"]).strip()
                branch_name = str(row["branch"]).strip()
                department_name = str(row["department"]).strip()

                # Skip completely empty rows.
                if not any((
                    student_id,
                    name,
                    branch_name,
                    department_name,
                )):
                    continue

                if not all((
                    student_id,
                    name,
                    branch_name,
                    department_name,
                )):
                    errors.append(
                        f"Row {row_number}: Missing required data."
                    )
                    continue

                # Find the branch within this institution.
                try:
                    branch = Branch.objects.get(
                        name__iexact=branch_name,
                        institution=upload.institution,
                    )
                except Branch.DoesNotExist:
                    errors.append(
                        f"Row {row_number}: Branch '{branch_name}' "
                        "not found in this institution."
                    )
                    continue
                except Branch.MultipleObjectsReturned:
                    errors.append(
                        f"Row {row_number}: Multiple branches match "
                        f"'{branch_name}'."
                    )
                    continue

                # Find the department within the selected branch.
                try:
                    department = Department.objects.get(
                        name__iexact=department_name,
                        branch=branch,
                    )
                except Department.DoesNotExist:
                    errors.append(
                        f"Row {row_number}: Department "
                        f"'{department_name}' not found in branch "
                        f"'{branch.name}'."
                    )
                    continue
                except Department.MultipleObjectsReturned:
                    errors.append(
                        f"Row {row_number}: Multiple departments match "
                        f"'{department_name}' in branch '{branch.name}'."
                    )
                    continue

                # Create or update the student.
                try:
                    StudentRecord.objects.update_or_create(
                        student_id=student_id,
                        defaults={
                            "name": name,
                            "branch": branch,
                            "department": department,
                            "institution": upload.institution,
                        },
                    )
                except Exception as exc:
                    errors.append(
                        f"Row {row_number}: Could not save student "
                        f"'{student_id}': {exc}"
                    )

        # 5. Update upload status.
        # Change this if your model uses a different status convention.
        upload.processed = not errors
        upload.save(update_fields=["processed"])

        return errors

    except Exception as exc:
        # Record the failure and re-raise it so the calling view/task
        # can display the error to the user.
        upload.processed = False
        upload.save(update_fields=["processed"])
        raise ValueError(f"Student upload failed: {exc}") from exc
