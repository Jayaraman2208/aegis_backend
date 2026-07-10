# 🛡️ Aegis Backend

🚀 **Live Demo:** [https://aegis-backend.onrender.com](https://aegis-backend.onrender.com)

# Aegis Backend â€” Django + MySQL

REST API for the Aegis tourist-safety app (SOS alerts, emergency contacts,
live risk zones, check-ins, geofences, and the "Ask Aegis" chatbot). Built
to sit directly behind the frontend prototype already delivered
(`aegis-app.html`).

## 1. Requirements

- Python 3.11+
- `pip install -r requirements.txt`

By default this project runs on **zero-config SQLite** â€” no database server
to install, no credentials to set up. Switch to MySQL any time by flipping
one flag (see step 5).

## 2. Fastest path â€” run it now

```bash
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env

python manage.py migrate
python manage.py seed_demo_data      # creates demo_traveler/demo12345 + contacts + 4 risk zones
python manage.py runserver
```

Open **http://127.0.0.1:8000/** â€” the app UI *and* the API are served from
this single command. It auto-logs in as `demo_traveler` on load, so there's
nothing else to configure to try every screen (Home, Map, SOS, Chat, Profile).

Admin panel: `http://127.0.0.1:8000/admin/` â€” create a superuser with
`python manage.py createsuperuser` to view/edit raw data there.

## 3. Switching to MySQL

```bash
mysql -u root -p < mysql_setup.sql   # creates aegis_db + aegis_user
```
Then in `.env`, set `USE_MYSQL=True` and fill in `DB_NAME` / `DB_USER` /
`DB_PASSWORD` / `DB_HOST` / `DB_PORT` (defaults match `mysql_setup.sql`).
`mysqlclient` needs native build tools first:
```bash
# Ubuntu/Debian
sudo apt-get install -y python3-dev default-libmysqlclient-dev build-essential pkg-config
# macOS
brew install mysql-client pkg-config
```
Re-run `migrate` and `seed_demo_data` against the new database, then `runserver`.

## 4. Deploying

`Procfile` is set up for Render/Railway/Heroku-style platforms:
```
release: python manage.py migrate && python manage.py seed_demo_data
web: gunicorn aegis_backend.wsgi --bind 0.0.0.0:$PORT
```
Static assets are served via WhiteNoise (already wired into `MIDDLEWARE`), so
no separate static file host is required. Before going live: set `DJANGO_DEBUG=False`,
a real `DJANGO_SECRET_KEY`, your real `DJANGO_ALLOWED_HOSTS`, and switch to MySQL.

## 5. Frontend notes

`templates/index.html` is the entire frontend â€” a phone-shaped single-page
app (vanilla JS, no build step) that calls the API at relative `/api/...`
paths, so there's no CORS configuration needed in production. It includes:
- a sliding pill indicator and directional slide transitions between tabs
- staggered card reveal animations replayed on every screen visit
- an animated safety-score ring, radar-pulse SOS button, and live typing
  indicator in chat
- a connection overlay that clearly reports the error and offers a retry
  button if the API can't be reached (rather than failing silently)

## 6. Authentication

JWT-based. Register, then log in to get an access token:

```bash
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -d '{"username":"mira","email":"mira@example.com","password":"strongpass123"}' \
  -H "Content-Type: application/json"

curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -d '{"username":"mira","password":"strongpass123"}' \
  -H "Content-Type: application/json"
# -> {"access": "...", "refresh": "..."}
```
Send the access token on every subsequent request:
`Authorization: Bearer <access_token>`

## 7. API reference

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/auth/register/` | POST | Create account |
| `/api/auth/login/` | POST | Get JWT access/refresh tokens |
| `/api/auth/refresh/` | POST | Refresh an expired access token |
| `/api/me/` | GET/PATCH | View or update profile + medical ID |
| `/api/contacts/` | GET/POST | List / add emergency contacts |
| `/api/contacts/{id}/` | PATCH/DELETE | Update / remove a contact |
| `/api/zones/` | GET | List all safety zones |
| `/api/zones/nearby/?lat=&lng=&radius_km=` | GET | Zones within radius, nearest first |
| `/api/incidents/` | GET/POST | Community incident reports |
| `/api/sos/` | POST | **Trigger an SOS alert** â€” fans out to all contacts |
| `/api/sos/active/` | GET | The caller's current active alert, if any |
| `/api/sos/{id}/resolve/` | POST | Mark alert resolved, or `{"cancelled": true}` |
| `/api/checkins/` | GET/POST | Manual "I'm here" check-ins |
| `/api/geofences/` | GET/POST/PATCH/DELETE | User-defined safe zones |
| `/api/chat/` | GET/POST | Chat history / send a message, get a bot reply |

### Example: trigger SOS
```bash
curl -X POST http://127.0.0.1:8000/api/sos/ \
  -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
  -d '{"latitude": 13.0827, "longitude": 80.2707, "address": "Old Town Market", "trigger_method": "button"}'
```
Response includes a `notifications` array â€” one row per emergency contact,
each with delivery status, mirroring the checklist animation in the
frontend prototype.

### Example: chat
```bash
curl -X POST http://127.0.0.1:8000/api/chat/ \
  -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
  -d '{"message": "nearest hospital"}'
```
Returns both the stored user message and the generated bot reply.

## 8. Notes on production-readiness

- SOS notification delivery (`SOSAlertViewSet.create`) is a synchronous stub.
  Wire it to Celery + an SMS/push provider (Twilio, FCM) before going live â€”
  emergency dispatch must never block on a slow HTTP request.
- `core/chatbot.py` is a keyword-matching placeholder so the API contract is
  stable; swap in a real NLP/LLM service behind the same `get_bot_reply()`
  function signature without touching views or the frontend.
- Safety-zone risk scores are static demo data here; in production these
  come from the ML risk-scoring pipeline described in the project brief.

