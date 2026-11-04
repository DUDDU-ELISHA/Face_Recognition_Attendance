import os
import sqlite3
from contextlib import contextmanager
from datetime import date

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if os.environ.get("VERCEL"):
    DB_PATH = os.environ.get("ATTENDANCE_DB_PATH", "/tmp/face-attendance/attendance.db")
else:
    DB_PATH = os.environ.get("ATTENDANCE_DB_PATH", os.path.join(BASE_DIR, "attendance.db"))

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            created_at TEXT NOT NULL
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            attendance_date TEXT NOT NULL,
            attendance_time TEXT NOT NULL,
            status TEXT NOT NULL,
            UNIQUE(student_id, attendance_date),
            FOREIGN KEY(student_id) REFERENCES students(student_id)
        )""")

def dashboard_stats():
    today = date.today().isoformat()
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        present = conn.execute("SELECT COUNT(*) FROM attendance WHERE attendance_date=?", (today,)).fetchone()[0]
    absent = max(total - present, 0)
    percentage = round((present / total) * 100, 1) if total else 0
    return {"total": total, "present": present, "absent": absent, "percentage": percentage}

def list_students(limit=None):
    query = "SELECT student_id, name, department, created_at FROM students ORDER BY name"
    if limit:
        query += f" LIMIT {int(limit)}"
    with get_db() as conn:
        return conn.execute(query).fetchall()

def list_attendance(selected_date):
    with get_db() as conn:
        return conn.execute("""
            SELECT a.student_id, s.name, s.department, a.attendance_date, a.attendance_time, a.status
            FROM attendance a JOIN students s ON s.student_id=a.student_id
            WHERE a.attendance_date=? ORDER BY a.attendance_time DESC
        """, (selected_date,)).fetchall()
