import base64
import os
import cv2
import numpy as np

def decode_image(image_data):
    if "," in image_data:
        image_data = image_data.split(",", 1)[1]
    try:
        raw = base64.b64decode(image_data)
        array = np.frombuffer(raw, dtype=np.uint8)
        image = cv2.imdecode(array, cv2.IMREAD_COLOR)
    except Exception:
        image = None
    if image is None:
        raise ValueError("Could not read the webcam image.")
    return image

def detect_face(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    detector = cv2.CascadeClassifier(cascade_path)
    faces = detector.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(80, 80))
    if len(faces) == 0:
        return None
    x, y, w, h = max(faces, key=lambda box: box[2] * box[3])
    face = gray[y:y+h, x:x+w]
    return cv2.resize(face, (200, 200))

def save_face_samples(student_id, image_data, dataset_dir):
    image = decode_image(image_data)
    face = detect_face(image)
    if face is None:
        raise ValueError("No face detected. Face the camera with good lighting.")
    student_dir = os.path.join(dataset_dir, student_id)
    os.makedirs(student_dir, exist_ok=True)
    existing = len([f for f in os.listdir(student_dir) if f.endswith(".jpg")])
    if existing >= 20:
        raise ValueError("20 face samples are already saved for this student.")
    path = os.path.join(student_dir, f"{existing + 1:02d}.jpg")
    cv2.imwrite(path, face)
    return existing + 1

def train_model(dataset_dir, model_path):
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    faces, labels = [], []
    label_to_id = {}
    label = 0
    for student_id in sorted(os.listdir(dataset_dir)):
        folder = os.path.join(dataset_dir, student_id)
        if not os.path.isdir(folder):
            continue
        student_images = 0
        for filename in sorted(os.listdir(folder)):
            if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
                continue
            image = cv2.imread(os.path.join(folder, filename), cv2.IMREAD_GRAYSCALE)
            if image is not None:
                faces.append(cv2.resize(image, (200, 200)))
                labels.append(label)
                student_images += 1
        if student_images:
            label_to_id[label] = student_id
            label += 1
    if len(faces) < 2:
        raise ValueError("Capture at least 2 face samples before training.")
    recognizer.train(faces, np.array(labels, dtype=np.int32))
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    recognizer.save(model_path)
    mapping_path = os.path.splitext(model_path)[0] + "_labels.txt"
    with open(mapping_path, "w", encoding="utf-8") as file:
        for key, value in label_to_id.items():
            file.write(f"{key}:{value}\n")
    return len(faces)

def recognize_face(image_data, model_path):
    image = decode_image(image_data)
    face = detect_face(image)
    if face is None:
        raise ValueError("No face detected. Move closer to the camera.")
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(model_path)
    label, confidence = recognizer.predict(face)
    mapping_path = os.path.splitext(model_path)[0] + "_labels.txt"
    mapping = {}
    with open(mapping_path, "r", encoding="utf-8") as file:
        for line in file:
            key, value = line.strip().split(":", 1)
            mapping[int(key)] = value
    if confidence > 65 or label not in mapping:
        return None, confidence
    return mapping[label], confidence
