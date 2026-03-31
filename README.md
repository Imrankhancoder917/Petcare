# 🐾 PetCare Connect Pro

A complete, advanced full-stack web application for animal welfare — enabling users to report injured/stray animals, volunteers to respond, and admins to monitor system activity.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML, CSS, Vanilla JavaScript |
| Charts | Chart.js |
| Maps | Google Maps JavaScript API |
| Backend | Python Flask (REST API) |
| Auth | JWT (Flask-JWT-Extended) |
| Database | MySQL (PyMySQL) |
| Real-time | Flask-SocketIO (WebSockets) |
| ML | TF-IDF + Logistic Regression (scikit-learn) |

---

## Project Structure

```
petcare/
├── README.md
├── .gitignore
├── frontend/
│   ├── index.html        # Home / report submission page
│   ├── login.html        # Signup & Login
│   ├── dashboard.html    # Reports dashboard with filters
│   ├── map.html          # Google Maps report visualisation
│   ├── admin.html        # Admin panel (analytics + user management)
│   ├── style.css         # Global responsive styles
│   └── script.js         # Shared JS helpers (auth, fetch, toast)
└── backend/
    ├── app.py            # Flask app entry point + SocketIO
    ├── config.py         # Configuration (env vars)
    ├── schema.sql        # MySQL DDL (run once to initialise DB)
    ├── requirements.txt  # Python dependencies
    ├── .env.example      # Sample environment variables
    ├── models/
    │   └── db.py         # DB connection + auto-create tables
    ├── routes/
    │   ├── auth.py       # POST /signup, POST /login
    │   ├── reports.py    # POST /report, GET /reports, PUT /update-status/:id
    │   ├── assignments.py# POST /assign/:report_id, GET /assignments
    │   └── analytics.py  # GET /analytics, GET /admin/users, PUT /admin/users/:id/role
    ├── ml/
    │   └── classifier.py # TF-IDF + Logistic Regression urgency classifier
    └── uploads/          # Uploaded images stored here
```

---

## Prerequisites

- Python 3.9+
- MySQL 8.0+ (or MariaDB 10.6+)
- A modern web browser
- (Optional) Google Maps API key

---

## Setup — Step by Step

### 1. Database

```bash
# Log in to MySQL
mysql -u root -p

# Run the schema file
SOURCE /path/to/petcare/backend/schema.sql;
```

This creates the `petcare_db` database, all tables, and a default admin account:
- **Email:** `admin@petcare.com`
- **Password:** `Admin@123`

### 2. Backend

```bash
cd backend

# Create & activate virtual environment
python -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your MySQL credentials & secret keys

# Start the server
python app.py
```

The API server runs at **http://localhost:5000**

### 3. Frontend

No build step needed — open the HTML files directly in a browser **or** serve them with any static server:

```bash
# Option A: Python built-in server
cd frontend
python -m http.server 8080
# Open http://localhost:8080/login.html

# Option B: VS Code Live Server extension
# Right-click login.html → Open with Live Server
```

### 4. Google Maps (Optional)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the **Maps JavaScript API**
3. Create an API key
4. In `frontend/map.html`, replace `YOUR_GOOGLE_MAPS_API_KEY` with your key

---

## API Reference

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/signup` | Register a new user |
| POST | `/login`  | Login and receive JWT token |

**Request body (both):**
```json
{ "name": "Alice", "email": "alice@example.com", "password": "secret123", "role": "user" }
```

**Response:**
```json
{ "token": "<jwt>", "role": "user", "name": "Alice" }
```

### Reports

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/report` | Any | Submit new report (multipart/form-data) |
| GET  | `/reports` | Any | List reports (filter by `?status=&urgency=`) |
| GET  | `/report/<id>` | Any | Get single report |
| PUT  | `/update-status/<id>` | Volunteer/Admin | Update report status |

### Assignments (Volunteers)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/assign/<report_id>` | Volunteer/Admin | Accept a case |
| GET  | `/assignments` | Volunteer/Admin | List assignments |

### Analytics & Admin

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/analytics` | Any | System statistics |
| GET | `/admin/users` | Admin | List all users |
| PUT | `/admin/users/<id>/role` | Admin | Update user role |

---

## Role Permissions

| Feature | User | Volunteer | Admin |
|---------|------|-----------|-------|
| Submit reports | ✅ | ✅ | ✅ |
| View reports/dashboard | ✅ | ✅ | ✅ |
| Accept a case | ❌ | ✅ | ✅ |
| Update case status | ❌ | ✅ (own) | ✅ |
| View admin panel | ❌ | ❌ | ✅ |
| Manage users | ❌ | ❌ | ✅ |

---

## ML Urgency Classifier

Located in `backend/ml/classifier.py`.

- Uses **TF-IDF vectorisation** (unigrams + bigrams, max 500 features)
- Trained with **Logistic Regression** on 40 labelled examples
- Includes a keyword-override layer for obvious HIGH-urgency terms (bleeding, injured, emergency, etc.)
- Model is trained **in-memory** on first request (no separate training step required)
- Returns `"HIGH"` or `"LOW"` urgency for any description text

---

## Real-time Notifications

Uses **Flask-SocketIO** with eventlet.

- When a new report is submitted via `index.html`, the client emits a `new_report` event
- The server broadcasts a `report_notification` event to all connected clients
- Volunteers receive a toast notification with the report title and urgency

---

## Database Schema

```sql
users       (id, name, email, password, role, created_at)
reports     (id, user_id, title, description, image, lat, lng, status, urgency, created_at)
assignments (id, report_id, volunteer_id, status, assigned_at)
```

Foreign key relationships:
- `reports.user_id` → `users.id`
- `assignments.report_id` → `reports.id`
- `assignments.volunteer_id` → `users.id`

---

## Security Notes

- Passwords are hashed with **bcrypt** (work factor 12) before storage
- JWT tokens expire after 24 hours
- File uploads are validated by extension; only images are accepted (max 16 MB)
- CORS is enabled for all origins in development — restrict in production
- Change `SECRET_KEY` and `JWT_SECRET_KEY` in `.env` before deploying