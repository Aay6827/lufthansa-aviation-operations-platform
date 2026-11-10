# Architecture Decision Record – Initial Platform

## Context
The portfolio must demonstrate a balanced junior software and DevOps engineering skill set through a realistic aviation maintenance workflow.

## Decisions
1. Start with a modular monolith in FastAPI. This keeps the first release maintainable and avoids distributed-systems complexity before it is needed.
2. Use PostgreSQL as the primary relational database.
3. Use SQLAlchemy 2 for persistence and introduce Alembic migrations before deployment.
4. Use React + TypeScript as a separate frontend application in Stage 2.
5. Containerize the API and database for repeatable local environments.
6. Target Azure Container Registry and AKS for cloud deployment, with Terraform and Helm.
7. Add health endpoints immediately; add Prometheus metrics, Grafana dashboards and OpenTelemetry tracing in the observability stage.

## Initial domain model
- Aircraft: registration, type, manufacturer and operational status.
- WorkOrder: unique work-order number, aircraft reference, description, priority, status and due date.

## Security and production considerations
The current release is a development scaffold. Before production-like deployment, add authentication and authorization, managed secrets, TLS, database migrations, structured logs, rate limiting, dependency scanning, image scanning, backups and least-privilege identities.
