# Smart Storage Locker Management System

A production-quality Django REST backend for managing smart storage lockers. Built with Django 5.x, PostgreSQL, Redis caching, JWT authentication, and structured logging for Kibana/ELK integration.

---

## 🏗️ Architecture Overview

```
smart_locker/
├── config/                  # Django project configuration
│   ├── settings.py          # All settings (DB, cache, JWT, logging)
│   ├── urls.py              # Root URL routing
│   ├── exceptions.py        # Custom exception handler
│   ├── wsgi.py              # WSGI entry point
│   └── asgi.py              # ASGI entry point
├── users/                   # User management & authentication
│   ├── models.py            # Custom User model with roles
│   ├── serializers.py       # Register, Login, Profile serializers
│   ├── views.py             # Auth endpoints
│   ├── permissions.py       # IsAdmin, IsOwnerOrAdmin
│   ├── backends.py          # Email authentication backend
│   └── tests.py             # Unit tests
├── lockers/                 # Locker management
│   ├── models.py            # Locker model (status, size, location)
│   ├── serializers.py       # Locker serializers
│   ├── views.py             # CRUD + Redis-cached available lockers
│   └── tests.py             # Unit tests
├── reservations/            # Reservation management
│   ├── models.py            # Reservation model with constraints
│   ├── serializers.py       # Create/Release with concurrency control
│   ├── views.py             # Reserve, release, list endpoints
│   └── tests.py             # Unit tests
├── logstash/                # Logstash pipeline configuration
│   └── pipeline/
│       └── logstash.conf    # Ships JSON logs → Elasticsearch
├── docker-compose.yml       # PostgreSQL, Redis, ELK stack
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (dev)
├── .env.example             # Environment template
└── README.md                # This file
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- pip

### 1. Clone & Setup

```bash
cd smart_locker

# Create virtual environment
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 2. Start Infrastructure (PostgreSQL, Redis, ELK)

```bash
docker-compose up -d
```

### 3. Run Migrations & Create Superuser

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### 4. Start Development Server

```bash
python manage.py runserver
```

The API is now running at **http://localhost:8000**

---

## 📚 API Endpoints

### Authentication & User Management

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| `POST` | `/api/auth/register/` | Public | Register new user |
| `POST` | `/api/auth/login/` | Public | Login (get JWT tokens) |
| `POST` | `/api/auth/refresh/` | Public | Refresh JWT access token |
| `GET` | `/api/auth/profile/` | Authenticated | Get user profile |
| `PUT` | `/api/auth/change-password/` | Authenticated | Change password |

### Locker Management

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| `POST` | `/api/lockers/` | Admin | Create a new locker |
| `GET` | `/api/lockers/` | Authenticated | List all lockers |
| `GET` | `/api/lockers/{id}/` | Authenticated | Get locker details |
| `PUT` | `/api/lockers/{id}/` | Admin | Update a locker |
| `DELETE` | `/api/lockers/{id}/` | Admin | Deactivate a locker |
| `GET` | `/api/lockers/available/` | Authenticated | List available lockers (Redis cached) |

### Reservation Management

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| `POST` | `/api/reservations/` | Authenticated | Reserve a locker |
| `GET` | `/api/reservations/` | Authenticated | List reservations (own / admin: all) |
| `GET` | `/api/reservations/{id}/` | Authenticated | Reservation details |
| `PUT` | `/api/reservations/{id}/release/` | Authenticated | Release a locker |

### Documentation & Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/docs/` | Swagger UI (interactive API docs) |
| `GET` | `/api/health/` | Health check |
| `GET` | `/admin/` | Django Admin Panel |

---

## 🔐 Authentication

This system uses **JWT (JSON Web Token)** authentication via `djangorestframework-simplejwt`.

### Register a User
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "securepass123",
    "password_confirm": "securepass123",
    "role": "user"
  }'
```

### Login
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "securepass123"
  }'
```

### Use the Access Token
```bash
curl -X GET http://localhost:8000/api/lockers/ \
  -H "Authorization: Bearer <access_token>"
```

### Refresh Token
```bash
curl -X POST http://localhost:8000/api/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "<refresh_token>"}'
```

---

## 🔑 Role-Based Access Control

| Role | Capabilities |
|------|--------------|
| **Admin** | Create/update/deactivate lockers, view all reservations, manage system |
| **User** | View lockers, reserve/release lockers, view own reservations |

---

## ⚡ Redis Caching Strategy

The **Available Lockers** endpoint uses Redis caching for performance:

1. **Cache Check**: On `GET /api/lockers/available/`, Redis is checked first
2. **Cache Hit**: Returns cached data immediately (response includes `"source": "cache"`)
3. **Cache Miss**: Queries PostgreSQL, stores result in Redis with **60-second TTL**
4. **Cache Expiry**: On reservation/release, cache expires naturally — no manual invalidation

The response includes a `source` field (`"cache"` or `"database"`) for visibility.

---

## 📊 Logging & Kibana Integration

### Structured JSON Logging

All application events are logged in JSON format to `logs/app.json.log`:
- Authentication attempts (login success/failure)
- Reservation actions (create, release)
- Admin operations (locker CRUD)
- Application errors

### Viewing Logs in Kibana

1. Start the ELK stack: `docker-compose up -d`
2. Open Kibana: **http://localhost:5601**
3. Create an index pattern: `smart-locker-logs-*`
4. View logs in the **Discover** tab

---

## 🛡️ Concurrency Control

Reservations use PostgreSQL's `SELECT ... FOR UPDATE` to prevent race conditions:

- When a user reserves a locker, the locker row is **locked** during the transaction
- This prevents two users from reserving the same locker simultaneously
- A database-level `UniqueConstraint` ensures only one active reservation per locker

---

## 🧪 Running Tests

```bash
python manage.py test
```

Tests cover:
- User registration and login
- Locker CRUD operations
- Reservation creation and release
- Role-based access control
- Concurrent reservation handling

---

## 📦 Database Models

### User
- `id` — Primary key
- `name` — Full name
- `email` — Unique, used for login
- `role` — `admin` or `user`
- `created_at` / `updated_at`


### Locker
- `id` — Primary key
- `locker_number` — Unique identifier (e.g., "A-101")
- `location` — Physical location
- `size` — `small`, `medium`, or `large`
- `status` — `available`, `occupied`, `maintenance`, `deactivated`
- `created_at` / `updated_at`

### Reservation
- `id` — Primary key
- `user` — Foreign key → User
- `locker` — Foreign key → Locker
- `status` — `active`, `released`, `expired`
- `reserved_at` / `released_at`
- `created_at` / `updated_at`
- **Constraint**: Only one active reservation per locker

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Framework | Django 5.x + Django REST Framework |
| Database | PostgreSQL 16 |
| Cache | Redis 7 |
| Authentication | JWT (djangorestframework-simplejwt) |
| Logging | Structured JSON → Logstash → Elasticsearch → Kibana |
| API Docs | drf-spectacular (Swagger/OpenAPI 3.0) |
| Rate Limiting | DRF throttling (30/min anon, 100/min auth) |

---

## 📜 License

This project was built as a backend assessment submission.
