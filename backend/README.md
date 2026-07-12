# AI Financial Intelligence Platform — Backend

FastAPI backend for the AI Financial Intelligence Platform. Built on top of Supabase PostgreSQL with Clean Architecture, async code, and full RBAC.

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI 0.115 |
| Language | Python 3.12 |
| Database | Supabase (PostgreSQL) |
| Auth | Supabase Auth + JWT |
| Validation | Pydantic v2 |
| Logging | Loguru |

## Project Structure

```
backend/
├── app/
│   ├── api/v1/          # FastAPI routers (one per module)
│   ├── auth/            # Signup, login, onboarding
│   ├── core/            # Config, logging, constants
│   ├── database/        # Supabase client factory
│   ├── dependencies/    # FastAPI DI: auth, RBAC
│   ├── exceptions/      # Base errors + HTTP exception handlers
│   ├── middleware/      # Logging, audit middleware
│   ├── repositories/    # DB access layer (wraps Supabase SDK)
│   ├── schemas/         # Pydantic v2 request/response models
│   ├── services/        # Business logic layer
│   └── main.py          # App factory
├── tests/
├── requirements.txt
└── .env.example
```

## Quick Start

### 1. Create virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Unix
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env with your Supabase credentials
```

### 4. Run the server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Open API docs

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Structure

All endpoints are versioned under `/api/v1/`.

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/signup` | Create new user account |
| POST | `/api/v1/auth/login` | Login and get JWT token |
| POST | `/api/v1/auth/logout` | Invalidate session |
| POST | `/api/v1/auth/onboard` | Create company after signup |
| GET  | `/api/v1/auth/me` | Get current user profile |

### Protected Routes

All non-auth routes require `Authorization: Bearer <token>` header plus `X-Company-ID: <uuid>` header.

## Running Tests

```bash
pytest tests/ -v
```

## Architecture

See the implementation plan for full architectural decisions. Key points:

1. **RLS-first**: User JWT is passed to Supabase on every request — RLS handles multi-tenancy automatically.
2. **Service role only for admin**: The service role client bypasses RLS — only used for admin/background operations.
3. **Audit logging**: All mutating operations are logged to `audit_logs` automatically.
4. **RBAC**: Permission checks use the `permissions` + `role_permissions` tables seeded in migration 007.
