# Lufthansa Aviation Operations & Engineering Platform

An independent portfolio project simulating aircraft maintenance and spare-parts operations. This project is not affiliated with, endorsed by, or an internal system of Lufthansa Group, Lufthansa Systems, or Lufthansa Technik.

## Current status

**Stage 1 – Backend foundation (in progress)**

- FastAPI application with versioned REST endpoints
- SQLAlchemy models for aircraft and maintenance work orders
- PostgreSQL via Docker Compose; SQLite fallback for local tests
- Liveness and database-readiness endpoints
- Initial API tests

## Architecture

React + TypeScript (planned) → FastAPI → PostgreSQL

Delivery platform (planned): GitHub Actions → Docker → Azure Container Registry → AKS, provisioned with Terraform and deployed with Helm. Observability: Prometheus, Grafana and OpenTelemetry.

## Run locally with Docker Compose

```bash
docker compose up --build
```

Open API documentation at http://localhost:8000/docs.

## Run backend tests locally

```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

## Initial API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health/live` | Process liveness |
| GET | `/health/ready` | Database readiness |
| POST | `/api/v1/aircraft` | Register aircraft |
| GET | `/api/v1/aircraft` | List aircraft; optional `status_filter` |
| GET | `/api/v1/aircraft/{id}` | Get aircraft |
| POST | `/api/v1/work-orders` | Create maintenance work order |
| GET | `/api/v1/work-orders` | List work orders; optional status and overdue filters |

## Example: create an aircraft

```bash
curl -X POST http://localhost:8000/api/v1/aircraft \\
  -H 'Content-Type: application/json' \\
  -d '{"registration":"D-AIXX","aircraft_type":"A320neo","manufacturer":"Airbus","status":"operational"}'
```

## Engineering principles

- Keep business logic testable and API contracts explicit.
- Validate input at the API boundary.
- Keep secrets out of source control; local Compose credentials are for development only.
- Use migrations rather than automatic schema creation before production deployment.
- Add CI gates before introducing cloud deployment.
