import os
import sqlite3


def _ensure_database(database_path):
    directory = os.path.dirname(database_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            course_id INTEGER PRIMARY KEY,
            course_name TEXT NOT NULL,
            credit_hours INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS enrollments (
            student_id INTEGER,
            course_id INTEGER,
            semester TEXT,
            score REAL
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM courses")
    courses_count = cursor.fetchone()[0]
    if courses_count == 0:
        cursor.executemany(
            "INSERT INTO courses (course_id, course_name, credit_hours) VALUES (?, ?, ?)",
            [
                (1, "Python Programming", 3),
                (2, "Database Systems", 3),
                (3, "Artificial Intelligence", 4),
            ],
        )

    cursor.execute("SELECT COUNT(*) FROM enrollments")
    enrollments_count = cursor.fetchone()[0]
    if enrollments_count == 0:
        cursor.executemany(
            "INSERT INTO enrollments (student_id, course_id, semester, score) VALUES (?, ?, ?, ?)",
            [
                (1001, 1, "2026-1", 88),
                (1001, 2, "2026-1", 91),
                (1002, 1, "2026-1", 95),
                (1002, 3, "2026-1", 89),
                (1003, 2, "2026-1", 72),
                (1004, 1, "2026-1", 84),
            ],
        )

    connection.commit()
    connection.close()


def extract_database(database_path):
    _ensure_database(database_path)

    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            e.student_id,
            e.course_id,
            c.course_name,
            c.credit_hours,
            e.semester,
            e.score
        FROM enrollments e
        JOIN courses c
            ON e.course_id = c.course_id
    """)

    data = cursor.fetchall()
    connection.close()
    return data


if __name__ == "__main__":
    data = extract_database("database/students.db")
    print(data)
