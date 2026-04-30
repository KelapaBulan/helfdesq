# helfdesq — Help Desk Ticketing System

A web-based IT help desk ticketing system built with Django and Django REST Framework. Features a real-time admin dashboard, ticket lifecycle management, role-based access, JWT authentication, and a soft-delete recycle bin.

---

## Features

- Submit and track support tickets
- Admin dashboard with live activity feed and real-time ticket updates (polling)
- Priority levels: Low, Medium, High, Critical — with sound alerts for critical tickets
- Status management: Open → In Progress → Resolved → Closed
- Assign tickets to staff users
- Soft delete with recycle bin (restore or permanently delete)
- JWT-based REST API
- Postman collection included
- Reset password and remember me function

---

## Requirements

- Python 3.10+
- pip
- Git

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/KelapaBulan/helfdesq.git
cd helfdesq
```

### 2. Create and activate a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the database

The project uses SQLite by default. Run migrations to set up the schema:

```bash
python manage.py migrate
```

### 5. Create a superuser (admin account)

```bash
python manage.py createsuperuser
```

Follow the prompts to set a username, email, and password. This account will have full admin access including the dashboard and recycle bin.

### 6. (Optional) Create staff users

Log in to the Django admin panel at `/admin/` and create additional users. Set `is_staff = True` for users who should appear in the ticket assignment dropdown.
Additionally, superusers can assign any user as a staff later.

### 7. Run the development server

```bash
python manage.py runserver
```

The app will be available at `http://127.0.0.1:8000/`.

---

## Project Structure

```
helfdesq/
├── helfdesk/               # Main Django app
│   ├── models.py           # Ticket, FAQ, TicketActivity models
│   ├── views.py            # All views and API endpoints
│   ├── urls.py             # URL routing
│   ├── serializers.py      # DRF serializers
│   ├── forms.py            # TicketForm, RegisterForm
│   ├── permissions.py      # Custom DRF permissions
│   └── templates/
│       └── tiket/          # HTML templates
├── helfdesq/               # Django project config (settings, urls, wsgi)
├── postman/                # Postman API collection
├── .postman/               # Postman environment
└── manage.py
```

---

## Key URLs

| URL | Description |
|-----|-------------|
| `/` | Home — redirects based on role |
| `/create/` | Submit a new ticket |
| `/my/` | View your own tickets |
| `/dashboard/` | User dashboard |
| `/admin-dashboard/` | Admin dashboard (superuser only) |
| `/deleted-tickets/` | Recycle bin (superuser only) |
| `/register/` | Register a new account |
| `/admin/` | Django admin panel |

### API Endpoints

| URL | Method | Description |
|-----|--------|-------------|
| `/api/tickets/` | GET, POST | List / create tickets |
| `/api/tickets/<id>/` | GET, PUT, DELETE | Ticket detail |
| `/api/ticket-stats/` | GET | Count by status |
| `/api/activity-feed/` | GET | Recent activity |
| `/api/tickets-since/<timestamp>/` | GET | New tickets since timestamp |
| `/api/ticket-updates/` | GET | Sync status/assignment changes |
| `/api/token/` | POST | Obtain JWT token |
| `/api/token/refresh/` | POST | Refresh JWT token |

---

## API Authentication

The REST API uses JWT. To authenticate:

```bash
# Get token
POST /api/token/
{
  "username": "your_username",
  "password": "your_password"
}

# Use token in requests
Authorization: Bearer <access_token>
```

A Postman collection is available in the `/postman/` folder for easy testing.

---

## Notes

- The admin dashboard auto-polls every 10 seconds for new tickets, status changes, and activity.
- Critical tickets trigger a sound alert (`static/sounds/alert.mp3`). Make sure this file exists.
- Deleting a ticket from the dashboard soft-deletes it (sets `deleted_at`). It can be restored from the recycle bin. Permanent deletion removes it from the database entirely.
- The activity feed timestamps display in WIB (UTC+7) in 24-hour format.
