# FaceFit

68% of males buy sunglasses that fundamentally look bad on their style of face. So unless you're a Brad Pitt or a Hrithik Roshan, in which case what you wear doesn't really matter, the most basic thing you can do is know which style of sunglasses look best on you.

FaceFit is a full-stack playground for helping people pick sunglasses that suit their unique face shape. A FastAPI backend pairs traditional landmark detection with optional vision-language models, while the React/Vite frontend overlays lightweight 3D frames on a live camera feed so users can see the difference instantly.

PS: 96.48% of males quote statistics out of their a**es.

## Why it stands out

- **Smart classification** – MediaPipe heuristics classify faces on-device, with optional OpenAI or Gemini fallbacks for richer analyses.
- **Actionable recommendations** – Every face shape receives hand-tuned “wear” and “avoid” frame lists so the guidance is immediately useful.
- **Immersive experience** – Three.js powers a responsive 3D overlay that tracks the camera stream to visualise how each style fits.
- **Modern DX** – Fast builds with Vite, typed request bodies with Pydantic, and clean API logging that the UI can surface in real time.

## Architecture at a glance

| Layer      | Tech                                       | Highlights |
| ---------- | ------------------------------------------ | ---------- |
| Frontend   | React, Vite, Tailwind CSS, Three.js        | Live video preview, API-driven overlays |
| Backend    | FastAPI, MediaPipe, NumPy, Pillow          | Landmark extraction, heuristic + VLM classification |
| Integrations | OpenAI GPT-4o, Gemini Pro Vision (optional) | Vision-language alternative to local inference |

## Getting started

### Prerequisites

- Python 3.12+
- Node.js 18+
- (Optional) OpenAI or Gemini API keys for cloud-based classification

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Set API keys when you want to call external models:

```bash
export OPENAI_API_KEY=your_key
export GEMINI_API_KEY=your_key
```

With the key configured, POST an image to `/api/analyze-face` with `method` set to `openai` or `gemini` to switch providers on the fly.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The development server proxies `/api` requests to `http://localhost:8000/api`. During production builds the app falls back to `https://facefit-nntu.onrender.com/api`. Override this with `VITE_API_BASE` if you have a different deployment target.

### Running the test & build suites

- Backend unit tests: `cd backend && pytest`
- Frontend production build: `cd frontend && npm run build`

MediaPipe (and OpenCV) are imported lazily so the backend tests can run even in minimal CI containers.

## Roadmap ideas

- Expand the recommendation engine with gender-neutral and prescription-friendly frame options.
- Add profile persistence so users can save their favourite frames.
- Bring in WebGL face-mesh refinement for more precise 3D alignment.

## Contributors

Created as a personal project exploring the intersection of computer vision and product design. Feedback and pull requests are always welcome!
