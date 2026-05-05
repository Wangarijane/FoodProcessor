# FoodProcessor Backend (MVP)

Backend API for a Food Processing Marketplace connecting:
- Smallholder Farmers
- Processing Hubs
- Retail Stores

Built with Django + DRF + JWT authentication.

## Tech Stack

- Python 3.x
- Django
- Django REST Framework
- SimpleJWT
- SQLite (default for MVP)

## Project Structure

- `core/` - Django project config (`settings.py`, `urls.py`)
- `api/` - Application domain logic (models, serializers, views, urls)
- `api_tests.http` - REST Client test collection for endpoints

## Environment Setup

Create your environment file from example:

```bash
cp .env.example .env
```

Required variables in `.env`:

- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`

Example:

```env
SECRET_KEY=your_secret_key_here
DEBUG=True
ALLOWED_HOSTS=*
```

## Installation & Run

1. Create and activate a virtual environment
2. Install dependencies
3. Run migrations
4. Start server

Typical commands:

```bash
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

Server runs at:
- `http://127.0.0.1:8000/`
- API root: `http://127.0.0.1:8000/api/`

## Authentication

JWT-based authentication is enabled.

- Register: `POST /api/auth/register/`
- Login: `POST /api/auth/login/`
- Refresh: `POST /api/auth/refresh/`

Use access token in protected requests:

```http
Authorization: Bearer <access_token>
```

## API Endpoints

### Produce
- `GET /api/produce/` - List produce
- `POST /api/produce/` - Create produce listing (Farmer only)

### Orders
- `GET /api/orders/` - List orders (role-filtered)
- `POST /api/orders/` - Place order (Retailer only)
- `PATCH /api/orders/{id}/status/` - Update status to `Processing` or `Completed` (Hub only)

### Farmer
- `GET /api/farmer/earnings/` - Completed earnings total (Farmer only)

## Testing Endpoints Quickly

Use the included REST Client file:

- Open `api_tests.http`
- Set `@baseUrl`
- Paste JWT into `@token`
- Run requests in order (register -> login -> protected routes)

## Notes for Frontend/Mobile Integration

- API responses are JSON and client-agnostic
- CORS is currently open for MVP (`CORS_ALLOW_ALL_ORIGINS=True`)
- For production, restrict CORS and set explicit allowed hosts/domains

## Production Hardening Checklist

- Set `DEBUG=False`
- Use a strong private `SECRET_KEY`
- Restrict `ALLOWED_HOSTS`
- Restrict `CORS_ALLOWED_ORIGINS`
- Use PostgreSQL (recommended)
- Run with Gunicorn/Uvicorn + reverse proxy (Nginx)
- Enable HTTPS and secure cookie/JWT handling policies
