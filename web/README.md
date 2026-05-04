# MKID-IFTS Web ETC

Portable V1 web interface for the MKID-IFTS exposure-time calculator and project explorer.

## Structure

- `web/api/`: FastAPI backend that wraps the existing `mkid_ifts_sim` package.
- `web/app/`: React/Vite frontend for the public website and interactive dashboard.

## Local Development

Install Python dependencies:

```bash
pip install -e ".[web,test]"
```

Run the API:

```bash
uvicorn web.api.main:app --reload --host 127.0.0.1 --port 8000
```

Run the frontend in a second terminal:

```bash
cd web/app
npm install
npm run dev
```

The Vite dev server proxies `/api` and `/figures` to `http://127.0.0.1:8000`.

## API Endpoints

- `GET /health`
- `GET /api/presets`
- `POST /api/snr-from-time`
- `POST /api/time-from-snr`
- `POST /api/optimize-config`
- `POST /api/observation-rates`
- `POST /api/compare-strategies`

The public API deliberately forbids filesystem paths and unknown configuration fields.

## Deployment

Recommended low-cost deployment:

1. Deploy `web/app` to Cloudflare Pages.
   - Build command: `npm run build`
   - Output directory: `dist`
   - Set `VITE_API_URL` to the backend URL, for example `https://api.mkid-ifts.shayaanauqil.ca`.
2. Deploy the Python backend to Render/Fly/Railway or another Python host.
   - Install command: `pip install -e ".[web]"`
   - Start command: `uvicorn web.api.main:app --host 0.0.0.0 --port $PORT`
   - Set `CORS_ORIGINS` to the frontend origin.

The backend can also serve the built frontend if `web/app/dist` exists, which is useful for single-service demos.

## Model Scope

V1 uses the analytical ETC path for speed and interactivity. It is a planning/demo tool based on current model assumptions, not a fully calibrated observatory ETC.
