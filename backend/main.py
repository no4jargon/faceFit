from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import base64
from PIL import Image
from io import BytesIO
import numpy as np
import mediapipe as mp
import os
from openai import OpenAI
import google.generativeai as genai
import builtins

# Capture log messages so the frontend can display them
LOGS: list[str] = []

def log(*args, **kwargs):
    message = " ".join(str(a) for a in args)
    LOGS.append(message)
    # keep only the last 100 lines
    if len(LOGS) > 100:
        del LOGS[0]
    builtins.print(*args, **kwargs)

# Client will be created lazily when needed so tests don't require API keys
client = None

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sunglasses recommendations
RECOMMENDATIONS = {
    "Egg": {"recommended": ["Most styles", "Aviator", "Square"], "avoid": ["Very narrow"]},
    "Round": {"recommended": ["Rectangle", "Square", "Wayfarer"], "avoid": ["Round", "Oval"]},
    "Square": {"recommended": ["Round", "Oval", "Aviator"], "avoid": ["Square", "Rectangle"]},
    "Rectangular": {"recommended": ["Large Wayfarers", "Round", "Oversized"], "avoid": ["Narrow", "Rectangle"]},
    "Inverted Triangle": {"recommended": ["Aviator", "Rimless", "Oval"], "avoid": ["Top-heavy frames"]},
    "Triangle": {"recommended": ["Cat-eye", "Rectangular", "Semi-rimless"], "avoid": ["Very narrow"]}
}

class AnalyzePayload(BaseModel):
    image: str  # base64 encoded string
    method: str
    api_key: str | None = None

mp_face_mesh = mp.solutions.face_mesh


def decode_image(data: str) -> np.ndarray:
    try:
        log("Decoding image data, length:", len(data))
        image_data = base64.b64decode(data)
        image = Image.open(BytesIO(image_data)).convert("RGB")
        log("Image decoded successfully")
        return np.array(image)  # RGB numpy array
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid image data") from e


def detect_landmarks(img: np.ndarray):
    # img is RGB numpy array
    log("Detecting face landmarks")
    with mp_face_mesh.FaceMesh(static_image_mode=True) as face_mesh:
        results = face_mesh.process(img)
        if not results.multi_face_landmarks:
            raise HTTPException(status_code=400, detail="No face detected")
        log("Landmarks detected")
        return results.multi_face_landmarks[0]


def extract_measurements(landmarks, img_shape):
    log("Extracting face measurements")
    h, w, _ = img_shape
    get_point = lambda idx: np.array([landmarks.landmark[idx].x * w, landmarks.landmark[idx].y * h])

    forehead_width = np.linalg.norm(get_point(10) - get_point(338))
    cheekbone_width = np.linalg.norm(get_point(454) - get_point(234))
    jaw_width = np.linalg.norm(get_point(152) - get_point(378))
    face_length = np.linalg.norm(get_point(10) - get_point(152))

    measurements = {
        "forehead_width": forehead_width,
        "cheekbone_width": cheekbone_width,
        "jaw_width": jaw_width,
        "face_length": face_length,
    }
    log("Measurements:", measurements)
    return measurements


def classify_face_shape(measurements):
    fw = measurements["forehead_width"]
    cw = measurements["cheekbone_width"]
    jw = measurements["jaw_width"]
    fl = measurements["face_length"]

    face_length_width_ratio = fl / cw
    forehead_jaw_ratio = fw / jw if jw else 0
    jaw_cheekbone_ratio = jw / cw if cw else 0

    log(
        "Ratios:",
        {
            "face_length_width": face_length_width_ratio,
            "forehead_jaw": forehead_jaw_ratio,
            "jaw_cheekbone": jaw_cheekbone_ratio,
        },
    )

    if face_length_width_ratio > 1.5:
        shape = "Rectangular"
    elif 1.3 <= face_length_width_ratio <= 1.6:
        if jaw_cheekbone_ratio < 0.9:
            shape = "Oval"
        else:
            shape = "Diamond"
    elif face_length_width_ratio <= 1.2:
        if jaw_cheekbone_ratio > 0.95:
            shape = "Square"
        elif forehead_jaw_ratio > 1.1:
            shape = "Heart"
        else:
            shape = "Round"
    else:
        shape = "Oval"
    log("Heuristic face shape:", shape)
    return shape


def classify_face_shape_vlm(image_b64: str, provider: str, api_key: str | None) -> str:
    """Classify face shape using a vision language model."""
    prompt = (
        "Classify the face into one of the following shapes: "
        "Egg, Round, Square, Rectangular, Inverted Triangle, Triangle. "
        "Take into account the forehead, cheekbones, jawline, and face length. "
        "Respond with only the shape name."
    )

    try:
        if provider == "openai":
            key = api_key or os.getenv("OPENAI_API_KEY")
            if not key:
                raise HTTPException(status_code=400, detail="OpenAI API key required")
            client = OpenAI(api_key=key)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
                        ],
                    }
                ],
            )
            return response.choices[0].message.content.strip()
        elif provider == "gemini":
            key = api_key or os.getenv("GEMINI_API_KEY")
            if not key:
                raise HTTPException(status_code=400, detail="Gemini API key required")
            genai.configure(api_key=key)
            model = genai.GenerativeModel("gemini-pro-vision")
            result = model.generate_content([prompt, image_b64])
            return result.text.strip()
        else:
            raise HTTPException(status_code=400, detail="Unknown provider")
    except HTTPException:
        raise
    except Exception as e:
        log("VLM API error:", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/analyze-face")
def analyze_face(payload: AnalyzePayload):
    log("Received request to /api/analyze-face with method", payload.method)
    img = decode_image(payload.image)
    landmarks = detect_landmarks(img)
    measurements = extract_measurements(landmarks, img.shape)

    if payload.method == "mediapipe":
        face_shape = classify_face_shape(measurements)
    elif payload.method in {"openai", "gemini"}:
        face_shape = classify_face_shape_vlm(payload.image, payload.method, payload.api_key or "")
    elif payload.method == "open_source":
        face_shape = classify_face_shape(measurements)
    else:
        raise HTTPException(status_code=400, detail="Invalid method")
    fw = measurements["forehead_width"]
    cw = measurements["cheekbone_width"]
    jw = measurements["jaw_width"]
    fl = measurements["face_length"]

    face_length_width_ratio = fl / cw if cw else 0
    forehead_jaw_ratio = fw / jw if jw else 0
    jaw_cheekbone_ratio = jw / cw if cw else 0

    rec = RECOMMENDATIONS.get(face_shape, {"recommended": [], "avoid": []})
    log("Returning analysis for shape:", face_shape)
    return {
        "face_shape": face_shape,
        "recommendations": rec,
        "ratios": {
            "face_length_width_ratio": face_length_width_ratio,
            "forehead_jaw_ratio": forehead_jaw_ratio,
            "jaw_cheekbone_ratio": jaw_cheekbone_ratio,
        }
    }


@app.get("/api/logs")
def get_logs():
    """Return recent backend log messages."""
    return {"logs": LOGS}
