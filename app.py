import os
import cv2
import numpy as np
from datetime import date, datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from database import init_db, get_db, dashboard_stats, list_students, list_attendance
from face_recognition import save_face_samples, train_model, recognize_face

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "temporary-development-key-change-me")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Vercel's deployment filesystem is read-only. /tmp is writable but ephemeral.
# For persistent attendance data, configure an external database and object storage.
if os.environ.get("VERCEL"):
    RUNTIME_DIR = os.path.join("/tmp", "face-attendance")
else:
    RUNTIME_DIR = BASE_DIR

DATASET_DIR = os.path.join(RUNTIME_DIR, "dataset", "students")
MODEL_DIR = os.path.join(RUNTIME_DIR, "trained_model")
MODEL_PATH = os.path.join(MODEL_DIR, "face_model.yml")

os.makedirs(DATASET_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)
init_db()

@app.route("/")
def dashboard():
    return render_template("dashboard.html", stats=dashboard_stats(), students=list_students(limit=5))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        student_id = request.form.get("student_id", "").strip()
        name = request.form.get("name", "").strip()
        department = request.form.get("department", "").strip()
        if not all([student_id, name, department]):
            flash("Please fill in all student details.", "error")
            return redirect(url_for("register"))
        with get_db() as conn:
            exists = conn.execute("SELECT id FROM students WHERE student_id=?", (student_id,)).fetchone()
            if exists:
                flash("That student ID is already registered.", "error")
                return redirect(url_for("register"))
            conn.execute(
                "INSERT INTO students(student_id, name, department, created_at) VALUES(?,?,?,?)",
                (student_id, name, department, datetime.now().isoformat(timespec="seconds"))
            )
        os.makedirs(os.path.join(DATASET_DIR, student_id), exist_ok=True)
        flash("Student details saved. Capture face samples to complete registration.", "success")
        return redirect(url_for("register"))
    return render_template("register.html")

@app.route("/api/capture", methods=["POST"])
def capture():
    data = request.get_json(silent=True) or {}
    student_id = str(data.get("student_id", "")).strip()
    image_data = data.get("image", "")
    if not student_id or not image_data:
        return jsonify(success=False, message="Student ID and webcam image are required."), 400
    with get_db() as conn:
        student = conn.execute("SELECT student_id FROM students WHERE student_id=?", (student_id,)).fetchone()
    if not student:
        return jsonify(success=False, message="Register the student details first."), 404
    try:
        count = save_face_samples(student_id, image_data, DATASET_DIR)
        return jsonify(success=True, count=count, message=f"Face sample saved ({count}/20).")
    except ValueError as exc:
        return jsonify(success=False, message=str(exc)), 400

@app.route("/api/train", methods=["POST"])
def train():
    try:
        total = train_model(DATASET_DIR, MODEL_PATH)
        return jsonify(success=True, message=f"Model trained using {total} face images.")
    except ValueError as exc:
        return jsonify(success=False, message=str(exc)), 400

@app.route("/recognition")
def recognition():
    return render_template("recognition.html")

@app.route("/api/recognize", methods=["POST"])
def recognize():
    data = request.get_json(silent=True) or {}
    image_data = data.get("image", "")
    if not image_data:
        return jsonify(success=False, message="No webcam image received."), 400
    if not os.path.exists(MODEL_PATH):
        return jsonify(success=False, message="No trained model found. Register students and train the model first."), 400
    try:
        student_id, confidence = recognize_face(image_data, MODEL_PATH)
    except ValueError as exc:
        return jsonify(success=False, message=str(exc)), 400
    if student_id is None:
        return jsonify(success=False, recognized=False, message="Face not recognized. Please try again.")
    with get_db() as conn:
        student = conn.execute("SELECT student_id, name, department FROM students WHERE student_id=?", (student_id,)).fetchone()
        if not student:
            return jsonify(success=False, message="Recognized ID is not in the student database.")
        today = date.today().isoformat()
        existing = conn.execute(
            "SELECT id FROM attendance WHERE student_id=? AND attendance_date=?",
            (student_id, today)
        ).fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO attendance(student_id, attendance_date, attendance_time, status) VALUES(?,?,?,?)",
                (student_id, today, datetime.now().strftime("%I:%M:%S %p"), "Present")
            )
            marked = True
        else:
            marked = False
    return jsonify(
        success=True, recognized=True, marked=marked,
        student={"student_id": student["student_id"], "name": student["name"], "department": student["department"]},
        confidence=round(float(confidence), 1),
        message="Attendance marked successfully." if marked else "Attendance was already marked today."
    )

@app.route("/records")
def records():
    selected_date = request.args.get("date", date.today().isoformat())
    return render_template("records.html", records=list_attendance(selected_date), selected_date=selected_date)

@app.route("/reports")
def reports():
    return render_template("reports.html", stats=dashboard_stats(), records=list_attendance(date.today().isoformat()))

@app.route("/api/students")
def api_students():
    return jsonify([dict(row) for row in list_students()])

if __name__ == "__main__":
    app.run(debug=True)
