import pandas as pd
import re


def validate_student(student):
    errors = []

    if not student.get("student_id"):
        errors.append("student_id is required")

    if not student.get("name"):
        errors.append("name is required")

    if pd.isna(student.get("age")):
        errors.append("age is required")
    else:
        if not isinstance(student.get("age"), int):
            errors.append("age must be an integer")
        else:
            if student.get("age") < 16 or student.get("age") > 100:
                errors.append("age must be between 16 and 100")

    if not student.get("email"):
        errors.append("email is required")
    else:
        email = student.get("email")

        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
            errors.append("email format is invalid")

    if not student.get("phone"):
        errors.append("phone is required")
    else:
        phone = str(student.get("phone"))

        if not phone.isdigit():
            errors.append("phone must contain only digits")
        elif len(phone) < 9 or len(phone) > 15:
            errors.append("phone must contain between 9 and 15 digits")

    return errors


if __name__ == "__main__":

    valid_student = {
        "student_id": 1001,
        "name": "Dhekra",
        "age": 22,
        "email": "dhekra@gmail.com",
        "phone": "777123456",
    }

    missing_phone = {
        "student_id": 1002,
        "name": "Sara",
        "age": 23,
        "email": "sara@gmail.com",
    }

    invalid_phone = {
        "student_id": 1003,
        "name": "Ali",
        "age": 21,
        "email": "ali@gmail.com",
        "phone": "77712abc456",
    }

    short_phone = {
        "student_id": 1004,
        "name": "Mona",
        "age": 25,
        "email": "mona@gmail.com",
        "phone": "12345",
    }

    print("Valid student:")
    print(validate_student(valid_student))

    print("Missing phone:")
    print(validate_student(missing_phone))

    print("Invalid phone:")
    print(validate_student(invalid_phone))

    print("Short phone:")
    print(validate_student(short_phone))
