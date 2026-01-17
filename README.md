# match.fm

Compare two Last.fm users and see how closely their listening tastes align. Celery + Redis handle background fetching to keep the UI fast.

## Setup
1) Create a virtualenv and install deps:
```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2) Configure environment:
```bash
cp .env.example .env
# set DJANGO_SECRET_KEY and LASTFM_API_KEY
```
- Local dev defaults to inline tasks when `DEBUG=1` (`CELERY_TASK_ALWAYS_EAGER=1`), so you can skip Redis/Celery. Set `CELERY_TASK_ALWAYS_EAGER=0` to exercise the background worker.

3) Run migrations:
```bash
python manage.py migrate
```

4) (Async mode only) Start Redis (example via Docker):
```bash
docker run -p 6379:6379 redis:7-alpine
```

5) (Async mode only) Run Celery worker:
```bash
celery -A taste_matchmaker worker -l info
```

6) Start Django server:
```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/`, enter two Last.fm usernames, and watch the loading page as the worker fetches data.

## Deployment (Render free tier)
- `.render.yaml` is included for a Render Python web service.
- Set env vars in Render:
  - `DJANGO_SECRET_KEY` (generate a long random string)
  - `LASTFM_API_KEY`
  - `DEBUG=0`
  - `ALLOWED_HOSTS` (optional; Render hostname auto-added)
  - `CELERY_TASK_ALWAYS_EAGER=1` (defaulted in `.render.yaml` so tasks run inline without Redis on free tier)
- Build command: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
- Start command: `gunicorn taste_matchmaker.wsgi:application`
- Static files are served via WhiteNoise; no extra CDN or Nginx config required on Render.
- If you later add Redis + a Celery worker service, set `CELERY_TASK_ALWAYS_EAGER=0` and add a worker process: `celery -A taste_matchmaker worker -l info`.

## Notes
- API calls are cached: user info (24h) and top artists (12h) per user+period+limit.
- Retries with exponential backoff happen on Last.fm API errors or rate limits.
- Tests:
```bash
python manage.py test
```
