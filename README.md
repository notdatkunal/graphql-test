# FastAPI GraphQL API

A FastAPI application with GraphQL (Strawberry) and Keycloak authentication.

## Stack

- **FastAPI** — async Python web framework
- **Strawberry GraphQL** — GraphQL library for Python
- **SQLAlchemy** — ORM / database layer
- **Keycloak** — identity and access management (OIDC / OAuth2)
- **Docker Compose** — runs Keycloak locally

## Getting Started

### Prerequisites

- Python 3.12+
- Docker & Docker Compose

### 1. Start Keycloak

```bash
docker compose up -d
```

Keycloak admin console: [http://localhost:8080](http://localhost:8080) (`admin` / `admin`)

### 2. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Run the server

```bash
python run.py
```

The API is available at [http://localhost:8000](http://localhost:8000).

- GraphQL playground: [http://localhost:8000/graphql](http://localhost:8000/graphql)
- Login endpoint: `POST /login`

### 4. Authenticate

```bash
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}'
```

Use the returned `access_token` as a Bearer token for authenticated GraphQL requests.
