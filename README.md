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
