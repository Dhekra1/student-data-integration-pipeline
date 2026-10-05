"""Local Flask application used to supply predictable API test data."""

from flask import Flask, jsonify, redirect, url_for


app = Flask(__name__)
STUDENTS = [
    {"student_id": 1001, "gpa": 3.45, "attendance": 92, "status": "Active"},
    {"student_id": 1002, "gpa": 3.80, "attendance": 88, "status": "Active"},
    {"student_id": 1003, "gpa": 2.70, "attendance": 65, "status": "Active"},
    {"student_id": 1004, "gpa": 3.20, "attendance": 78, "status": "Active"},
]


@app.get("/")
def home() -> object:
    """Redirect the root endpoint to student API data.

    Returns:
        object: Flask redirect response.
    """
    return redirect(url_for("get_students"))


@app.get("/students")
def get_students() -> object:
    """Return deterministic student enrichment data.

    Returns:
        object: Flask JSON response.
    """
    return jsonify(STUDENTS)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)