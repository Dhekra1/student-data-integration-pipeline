from flask import Flask, jsonify

app = Flask(__name__)


students = [
    {"student_id": 1001, "gpa": 3.45, "attendance": 92, "status": "Active"},
    {"student_id": 1002, "gpa": 3.80, "attendance": 88, "status": "Active"},
    {"student_id": 1003, "gpa": 2.70, "attendance": 65, "status": "Active"},
    {"student_id": 1004, "gpa": 3.20, "attendance": 78, "status": "Active"},
]


@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "API is running", "endpoints": ["/students"]})


@app.route("/students", methods=["GET"])
def get_students():
    return jsonify(students)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
