import sqlite3


connection = sqlite3.connect("database/students.db")

cursor = connection.cursor()


# Create courses table
cursor.execute("""
CREATE TABLE IF NOT EXISTS courses (
    course_id INTEGER PRIMARY KEY,
    course_name TEXT NOT NULL,
    credit_hours INTEGER
)
""")


# Create enrollments table
cursor.execute("""
CREATE TABLE IF NOT EXISTS enrollments (
    student_id INTEGER,
    course_id INTEGER,
    semester TEXT,
    score REAL
)
""")


# Courses data
courses = [
    (1, "Python Programming", 3),
    (2, "Database Systems", 3),
    (3, "Artificial Intelligence", 4)
]


# Enrollments data
enrollments = [
    (1001, 1, "2026-1", 88),
    (1001, 2, "2026-1", 91),
    (1002, 1, "2026-1", 95),
    (1002, 3, "2026-1", 89),
    (1003, 2, "2026-1", 72),
    (1004, 1, "2026-1", 84)
]


# Insert courses and enrollments only if tables are empty to avoid UNIQUE errors
cursor.execute("SELECT COUNT(*) FROM courses")
courses_count = cursor.fetchone()[0]

if courses_count == 0:
    cursor.executemany(
        "INSERT INTO courses VALUES (?, ?, ?)",
        courses
    )

cursor.execute("SELECT COUNT(*) FROM enrollments")
enrollments_count = cursor.fetchone()[0]

if enrollments_count == 0:
    cursor.executemany(
        "INSERT INTO enrollments VALUES (?, ?, ?, ?)",
        enrollments
    )

connection.commit()
connection.close()

print("Database created/seeded successfully.")