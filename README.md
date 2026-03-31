# Grief Tracker

A Django REST API that replaces the Excel-based logistics issue workflow.
Built with **Python 3.14**, **uv**, and **Docker**.

---

## Project layout

```
grief-tracker/
├── Dockerfile
├── docker-compose.yml          # production stack (postgres + gunicorn)
├── docker-compose.dev.yml      # override for local dev (runserver)
├── pyproject.toml              # uv / PEP 621 project definition
├── manage.py
├── .env.example                # copy to .env before first run
│
├── config/
│   ├── settings/
│   │   ├── base.py             # shared: DRF, JWT, Spectacular
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   └── wsgi.py
│
└── apps/
    ├── accounts/               # Custom User model + JWT auth
    ├── grief/                  # GriefIssue + reference tables
    ├── imports/                # Excel importer (service + API upload)
    └── analytics/              # KPI & breakdown endpoints
```

---

## Quick start (Docker — recommended)

```bash
# 1. Clone and configure
cp .env.example .env          # edit SECRET_KEY and passwords

# 2. Start in development mode (live-reload)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# 3. First-time setup (in a second terminal)
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser

# 4. Import your Excel data
docker compose exec web python manage.py import_excel data/Grief_003.xlsm

# 5. Open the API docs
open http://localhost:8000/api/docs/
```

---

## Quick start (local, no Docker)

```bash
# Requires uv: https://docs.astral.sh/uv/getting-started/installation/

uv sync                                          # create .venv + install deps
source .venv/bin/activate

cp .env.example .env                             # edit DATABASE_URL for local postgres

python manage.py migrate
python manage.py createsuperuser
python manage.py import_excel data/Grief_003.xlsm
python manage.py runserver
```

---

## API overview

All endpoints are under `/api/v1/`. Authentication uses **JWT Bearer tokens**.

### Auth (`/api/v1/auth/`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/token/` | Obtain access + refresh tokens |
| POST | `/token/refresh/` | Refresh access token |
| POST | `/register/` | Create account (role: viewer) |
| GET/PATCH | `/me/` | View / update own profile |
| POST | `/me/change-password/` | Change password |
| GET | `/users/` | List all users (admin only) |

### Grief issues (`/api/v1/grief/`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/issues/` | Paginated, filterable list |
| POST | `/issues/` | Create issue (manager+) |
| GET | `/issues/<id>/` | Retrieve detail |
| PATCH | `/issues/<id>/` | Update (manager+) |
| DELETE | `/issues/<id>/` | Delete (admin only) |
| GET | `/issue-types/` | Reference list |
| GET | `/carriers/` | Reference list |
| GET | `/locations/` | Reference list |

#### Filters for `/issues/`

```
?status=SOLVED
?status=ONGOING
?carrier_name=Transmec
?issue_code=NO+LABELS
?causing_party=SUPPLIER
?year=2025&month=1
?date_from=2025-01-01&date_to=2025-03-31
?supplier=Carraro
?search=5014641074          # searches kn_ref, ship_id, to_ref, supplier, note
?ordering=-date             # any model field, prefix - for desc
```

### Analytics (`/api/v1/analytics/`)

All analytics endpoints accept the same filter params as issues.

| Path | Description |
|------|-------------|
| `/kpi/` | Total / solved / ongoing / solve rate / avg resolution days |
| `/by-carrier/` | Instances + % per carrier |
| `/by-issue-type/` | Instances + % per issue type |
| `/by-causing-party/` | Supplier / Carrier / Mixed breakdown |
| `/by-month/` | Monthly trend |
| `/by-location/` | Instances + % per location code |

### Import (`/api/v1/imports/`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/upload/` | Upload `.xlsx`/`.xlsm` (admin only, multipart) |

---

## User roles

| Role | Permissions |
|------|-------------|
| `viewer` | Read-only access to all data |
| `operator` | Read-only (same as viewer — extend as needed) |
| `manager` | Create and update grief issues |
| `admin` | Full access including delete + upload |

---

## Development

```bash
# Code quality
uv run ruff check .
uv run ruff format .
uv run mypy .

# Tests
uv run pytest

# Coverage
uv run coverage run -m pytest && uv run coverage report
```

---

## Import command reference

```bash
# Preview what the file contains without writing anything
python manage.py import_excel data/Grief_003.xlsm --dry-run

# Full import
python manage.py import_excel data/Grief_003.xlsm

# Safe to re-run — existing records (matched by unique_key) are skipped
```

---

## API docs

| URL | Description |
|-----|-------------|
| `/api/docs/` | Swagger UI |
| `/api/redoc/` | ReDoc |
| `/api/schema/` | Raw OpenAPI schema |
| `/admin/` | Django admin |
