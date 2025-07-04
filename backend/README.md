# FaceFit Backend

This directory contains the FastAPI service used by the FaceFit app.

## Local development

Create a virtual environment and install the requirements:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Run the API:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Making the API publicly accessible

When the React frontend is deployed (for example on Vercel) it needs to reach the API through a public URL. You can either deploy the API somewhere or expose your local server via a tunnel.

### Deploy to a server

Run the same `uvicorn` command on a publicly reachable machine or host it on a service such as Render, Fly.io or AWS. Update the frontend configuration to point to that public domain.

### Expose with ngrok

For quick testing you can keep the API running locally and expose it using [ngrok](https://ngrok.com):

```bash
ngrok http 8000
```

ngrok will print a URL such as `https://abcd1234.ngrok.io` that forwards requests to your local server. Set this URL in the frontend (e.g. `https://abcd1234.ngrok.io/api`) so it can call the backend.

If the backend is served on a different domain than the frontend, enable CORS in `main.py` so browsers can make requests across origins.
