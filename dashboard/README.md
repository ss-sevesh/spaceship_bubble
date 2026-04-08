# Spaceship Bubble — Research Dashboard

Immersive React dashboard for the **AI-driven Casimir Stiction-Suppressing Chiral Tellurium Metamaterials** project.

## Stack

- **Vite** — build tool and dev server (port 5173)
- **React Three Fiber / Three.js** — 3D metamaterial visualizer
- **Framer Motion** — kinetic UI and staggered animations
- **Lucide React** — iconography
- **FastAPI backend** — `server.py` on port 8000 (Vite proxies `/api` → `localhost:8000`)

## Launch

```bash
# Terminal 1 — FastAPI backend
cd dashboard
uv run python server.py        # runs on http://localhost:8000

# Terminal 2 — React dev server
cd dashboard
npm install
npm run dev                    # runs on http://localhost:5173
```

Open http://localhost:5173.

## Features

| Feature | Description |
|---|---|
| 3D Metamaterial Visualizer | Interactive Three.js scene — Te chiral plate + WTe₂ substrate |
| Pareto Design Table | 50-solution NSGA-II Pareto front; thermal fraction traffic-light coloring |
| Plot Gallery | 12 publication figures (Casimir curves, aniso, chiral, force, finite-T, 2-osc, Td-WTe₂, Au/SiO₂) |
| Re-Optimize | Triggers `main.py --optimize --plot` via FastAPI; polls `/api/status` every 3s until complete |
| Download Report | Exports selected Pareto design as a `.txt` spec file with full physics metadata |
| System Status | Live API connection indicator (green = backend online) |

## API Endpoints (server.py)

| Endpoint | Method | Description |
|---|---|---|
| `/api/status` | GET | Returns `{"status": "idle"/"busy", "error": null, "paths_verified": {...}}` |
| `/api/run-simulation` | POST | Triggers optimizer run (`--optimize --plot`), returns `{"status": "Simulation started"}` |
| `/api/results` | GET | Returns `pareto_results.json` as JSON |

## Notes

- `API_URL` in `App.jsx` uses `'/api'` (relative) — Vite proxies to `localhost:8000` via `vite.config.js`
- Re-Optimize timeout: 600s (optimizer takes 2–5 min for 50 Pareto solutions)
- Static fallback: if backend is offline, dashboard reads `/data/pareto_results.json` directly
