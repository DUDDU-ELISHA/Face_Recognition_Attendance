# Face Recognition Attendance Management System

A beginner-friendly attendance website built with Python, Flask, OpenCV LBPH face recognition, SQLite, HTML, CSS and JavaScript.

## Requirements
- Windows 10/11
- Python 3.10 or 3.11 recommended
- Webcam
- Chrome or Edge

## Setup on Windows

Open Command Prompt inside this project folder.

```bash
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

Open this address in Chrome:

http://127.0.0.1:5000

## How to use
1. Open **Register Student**.
2. Enter a unique Student ID, name and department. Click **Save Student Details**.
3. Enter the same Student ID in the Face Enrollment field.
4. Click **Start Camera**, allow camera access, then click **Capture Face** repeatedly. Capture up to 20 samples. Slightly change your head angle and expression between samples.
5. Repeat for each student.
6. Click **Train Recognition Model** after capturing samples for all students.
7. Open **Face Recognition**, start the camera and click **Scan & Mark Attendance**.
8. Open **Attendance Records** to view attendance for a selected date.

## Important notes
- Webcam access works on `localhost` or HTTPS. Use `http://127.0.0.1:5000` on the same computer.
- This starter uses OpenCV's LBPH recognizer. It is suitable for learning and demos, not high-security identity verification.
- Recognition accuracy depends on lighting, camera quality, face samples and similar-looking faces. Test carefully before relying on results.
- Capture only with the students' informed consent. Store face images securely, restrict access, and provide a way to delete a student's images and records. Face data is sensitive biometric information.
- Attendance is marked at most once per student per calendar day.
- To reset the demo, stop the app and delete `attendance.db`, `dataset/students/` contents and `trained_model/` contents.
- For deployment beyond your own computer, add authentication, HTTPS, authorization, audit logs, data retention controls and stronger anti-spoofing checks. Do not expose the Flask development server to the public internet.


## Vercel deployment (demo / testing)

This project includes `api/index.py` and `vercel.json` for Vercel's Python
function routing. Push this folder's contents to the root of a GitHub
repository, import that repository into Vercel, and deploy.

### Important storage limitation

The Vercel adaptation writes SQLite, face samples and the trained LBPH model
under `/tmp` so the function can start without trying to write to the
read-only deployment directory. `/tmp` is temporary and can be cleared or
isolated between serverless instances. Therefore student registrations,
attendance, face samples and trained models are NOT durable or reliable on
Vercel with this configuration. This ZIP is suitable for checking that the
Flask app routes/templates can deploy, not for running a real attendance
system. For real use, migrate SQLite to a hosted persistent database and
store face images/model artifacts in persistent object storage, then update
the app to use those services.

### Webcam and security notes

Deploy over HTTPS so browser camera access can work. Set a strong `SECRET_KEY`
in Vercel Project Settings > Environment Variables. This starter has no
authentication/authorization layer; do not expose student biometric data
publicly. Obtain informed consent and restrict access to face data.
