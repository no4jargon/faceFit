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

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
        print("Decoding image data, length:", len(data))
        image_data = base64.b64decode(data)
        image = Image.open(BytesIO(image_data)).convert("RGB")
        print("Image decoded successfully")
        return np.array(image)  # RGB numpy array
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid image data") from e


def detect_landmarks(img: np.ndarray):
    # img is RGB numpy array
    print("Detecting face landmarks")
    with mp_face_mesh.FaceMesh(static_image_mode=True) as face_mesh:
        results = face_mesh.process(img)
        if not results.multi_face_landmarks:
            raise HTTPException(status_code=400, detail="No face detected")
        print("Landmarks detected")
        return results.multi_face_landmarks[0]


def extract_measurements(landmarks, img_shape):
    print("Extracting face measurements")
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
    print("Measurements:", measurements)
    return measurements


def classify_face_shape(measurements):
    fw = measurements["forehead_width"]
    cw = measurements["cheekbone_width"]
    jw = measurements["jaw_width"]
    fl = measurements["face_length"]

    face_length_width_ratio = fl / cw
    forehead_jaw_ratio = fw / jw if jw else 0
    jaw_cheekbone_ratio = jw / cw if cw else 0

    print(
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
    print("Heuristic face shape:", shape)
    return shape


def classify_face_shape_vlm(image_b64: str) -> str:
    """Classify face shape using OpenAI's vision model."""
    print("Using OpenAI VLM for face shape classification...")
    print("OpenAI API key is set.")
    prompt = (
        "Classify the face into one of the following shapes: "
        "Egg, Round, Square, Rectangular, Inverted Triangle, Triangle"
        "Take into account the forehead, cheekbones, jawline, and face length."
        "And shadows, lighting, and other factors that may affect the appearance of the face."
        "Respond with only the shape name."
    )

    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=[{
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{image_b64}",
                    },
                ],
            }],
        )
        text = response.output_text
        return text
    except Exception as e:
        print("OpenAI API error:", e)
        raise HTTPException(status_code=500, detail="OpenAI API call failed") from e


@app.post("/api/analyze-face")
def analyze_face(payload: ImagePayload):
    print("Received request to /api/analyze-face")
    img = decode_image(payload.image)
    landmarks = detect_landmarks(img)
    measurements = extract_measurements(landmarks, img.shape)
    heuristic_shape = classify_face_shape(measurements)
    vlm_shape = classify_face_shape_vlm(payload.image)
    print("VLM classification:", vlm_shape)
    face_shape = vlm_shape
    fw = measurements["forehead_width"]
    cw = measurements["cheekbone_width"]
    jw = measurements["jaw_width"]
    fl = measurements["face_length"]

    face_length_width_ratio = fl / cw if cw else 0
    forehead_jaw_ratio = fw / jw if jw else 0
    jaw_cheekbone_ratio = jw / cw if cw else 0

    rec = RECOMMENDATIONS.get(face_shape, {})
    print("Returning analysis for shape:", face_shape)
    return {
        "face_shape": face_shape,
        "recommendations": rec,
        "ratios": {
            "face_length_width_ratio": face_length_width_ratio,
            "forehead_jaw_ratio": forehead_jaw_ratio,
            "jaw_cheekbone_ratio": jaw_cheekbone_ratio,
        }
    }
