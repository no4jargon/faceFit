# FaceFit

Simple face shape detector and sunglasses recommendation app.

## Development

### Backend

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Set `OPENAI_API_KEY` in your environment to enable the optional endpoint that
uses OpenAI's vision model:

```bash
export OPENAI_API_KEY=your_key
```

When the key is set, POSTing an image to `/api/analyze-face-vlm` will classify
the face using OpenAI instead of the built-in model.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend uses [Three.js](https://threejs.org/) for a 3D overlay on the live
camera stream. Running `npm install` will install this dependency automatically.

### API base URL

When running the development servers locally (`uvicorn` and `npm run dev`) the
frontend automatically calls `http://localhost:8000/api`. During a production
build the API base defaults to `https://facefit-nntu.onrender.com/api`. You can
override this by setting the `VITE_API_BASE` environment variable when starting
Vite or building the app.
