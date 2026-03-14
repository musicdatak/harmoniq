# HarmoniQ

Harmonic music scheduling web app built on the Camelot Wheel system. Import track lists, enrich with key/BPM/energy data, and generate optimally ordered playlists for smooth harmonic transitions.

## Quick Start

```bash
# Start backend + PostgreSQL
docker-compose up --build -d

# Start frontend dev server
cd frontend && npm install && npm run dev
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

## Tech Stack

**Backend**
- Python 3.10, FastAPI, async SQLAlchemy 2.0, asyncpg
- PostgreSQL 15, Alembic migrations
- JWT auth (access + refresh tokens), bcrypt
- MusicBrainz API integration (rate-limited)
- Essentia (tensorflow) server-side audio analysis
- Camelot Wheel harmonic engine + greedy nearest-neighbor scheduler

**Frontend**
- React 18, Vite, Tailwind CSS 3
- Essentia.js (WASM) for client-side audio analysis
- Axios with JWT interceptor (auto-refresh)
- Dark theme with DM Sans / JetBrains Mono

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://harmoniq:harmoniq@db:5432/harmoniq` | PostgreSQL connection |
| `JWT_SECRET_KEY` | `change-me-in-production` | JWT signing key |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token TTL |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token TTL |
| `CORS_ORIGINS` | `http://localhost:5173` | Allowed CORS origins |
| `MUSICBRAINZ_USER_AGENT` | `HarmoniQ/1.0.0 (contact@harmoniq.app)` | MusicBrainz API user agent |

## Workflow

1. **Import** — Upload Excel/CSV or paste text track list (Artist - Title)
2. **Enrich** — MusicBrainz lookup, server audio analysis (Essentia), or browser analysis (Essentia.js WASM). Inline edit key/BPM/energy overrides.
3. **Customize** — Set harmony/energy/BPM weights, toggle Energy Arc mode
4. **Results** — View mix score gauge, Camelot Wheel visualization, transition-annotated track order. Export as Excel or copy as text.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/register` | Register |
| POST | `/api/auth/login` | Login |
| POST | `/api/auth/refresh` | Refresh token |
| GET | `/api/auth/me` | Current user |
| GET/POST | `/api/playlists` | List / create playlists |
| GET/PUT/DELETE | `/api/playlists/{id}` | Playlist CRUD |
| POST | `/api/playlists/{id}/import/text` | Import from text |
| POST | `/api/playlists/{id}/import/excel` | Import from file |
| POST | `/api/playlists/{id}/enrich/musicbrainz` | Start MusicBrainz lookup |
| GET | `/api/playlists/{id}/enrich/status` | Enrichment progress |
| POST | `/api/playlists/{id}/schedule` | Run scheduler |
| GET | `/api/playlists/{id}/export/excel` | Export XLSX |
| GET | `/api/playlists/{id}/export/text` | Export text |
| POST | `/api/tracks/{id}/analyze` | Server audio analysis |
| PUT | `/api/tracks/{id}/update-analysis` | Browser analysis results |
| PUT | `/api/playlists/{id}/tracks/{trackId}` | Override key/BPM/energy |

## Running Tests

```bash
docker-compose exec backend python -m pytest tests/ -v
```
