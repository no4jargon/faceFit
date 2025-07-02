from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import base64
from PIL import Image
from io import BytesIO
import numpy as np
import cv2
import mediapipe as mp

app = FastAPI()

# Sunglasses recommendations
RECOMMENDATIONS = {
    "Oval": {"recommended": ["Square", "Rectangle", "Aviator"], "avoid": ["Oversized"]},
    "Round": {"recommended": ["Rectangle", "Square", "Cat-eye"], "avoid": ["Round"]},
    "Square": {"recommended": ["Round", "Oval", "Aviator"], "avoid": ["Square"]},
    "Rectangular": {"recommended": ["Large Wayfarers", "Aviator", "Round"], "avoid": ["Narrow"]},
    "Heart": {"recommended": ["Aviator", "Round", "Cat-eye"], "avoid": ["Oversized"]},
    "Diamond": {"recommended": ["Oval", "Cat-eye"], "avoid": ["Very Narrow"]},
}

class ImagePayload(BaseModel):
    image: str  # base64 encoded string

mp_face_mesh = mp.solutions.face_mesh


def decode_image(data: str) -> np.ndarray:
    try:
        image_data = base64.b64decode(data)
        image = Image.open(BytesIO(image_data)).convert("RGB")
        return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid image data") from e


def detect_landmarks(img: np.ndarray):
    with mp_face_mesh.FaceMesh(static_image_mode=True) as face_mesh:
        results = face_mesh.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        if not results.multi_face_landmarks:
            raise HTTPException(status_code=400, detail="No face detected")
        return results.multi_face_landmarks[0]


def extract_measurements(landmarks, img_shape):
    h, w, _ = img_shape
    get_point = lambda idx: np.array([landmarks.landmark[idx].x * w, landmarks.landmark[idx].y * h])

    forehead_width = np.linalg.norm(get_point(10) - get_point(338))
    cheekbone_width = np.linalg.norm(get_point(454) - get_point(234))
    jaw_width = np.linalg.norm(get_point(152) - get_point(378))
    face_length = np.linalg.norm(get_point(10) - get_point(152))

    return {
        "forehead_width": forehead_width,
        "cheekbone_width": cheekbone_width,
        "jaw_width": jaw_width,
        "face_length": face_length,
    }


def classify_face_shape(measurements):
    fw = measurements["forehead_width"]
    cw = measurements["cheekbone_width"]
    jw = measurements["jaw_width"]
    fl = measurements["face_length"]

    face_length_width_ratio = fl / cw
    forehead_jaw_ratio = fw / jw if jw else 0
    jaw_cheekbone_ratio = jw / cw if cw else 0

    if face_length_width_ratio > 1.5:
        return "Rectangular"
    elif 1.3 <= face_length_width_ratio <= 1.6:
        if jaw_cheekbone_ratio < 0.9:
            return "Oval"
        else:
            return "Diamond"
    elif face_length_width_ratio <= 1.2:
        if jaw_cheekbone_ratio > 0.95:
            return "Square"
        elif forehead_jaw_ratio > 1.1:
            return "Heart"
        else:
            return "Round"
    return "Oval"


@app.post("/api/analyze-face")
def analyze_face(payload: ImagePayload):
    img = decode_image(payload.image)
    landmarks = detect_landmarks(img)
    measurements = extract_measurements(landmarks, img.shape)
    face_shape = classify_face_shape(measurements)
    fw = measurements["forehead_width"]
    cw = measurements["cheekbone_width"]
    jw = measurements["jaw_width"]
    fl = measurements["face_length"]

    face_length_width_ratio = fl / cw if cw else 0
    forehead_jaw_ratio = fw / jw if jw else 0
    jaw_cheekbone_ratio = jw / cw if cw else 0

    rec = RECOMMENDATIONS.get(face_shape, {})
    return {
        "face_shape": face_shape,
        "recommendations": rec,
        "ratios": {
            "face_length_width_ratio": face_length_width_ratio,
            "forehead_jaw_ratio": forehead_jaw_ratio,
            "jaw_cheekbone_ratio": jaw_cheekbone_ratio,
        }
    }
