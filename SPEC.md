# Disney Page Update Notifier - Specification v0.3

---

## 1. Overview

This project monitors a specific section of the Tokyo Disney Resort website
and sends push notifications when changes are detected.

Frontend: Expo (React Native)  
Backend: FastAPI (Python)  
Database: PostgreSQL  
Deployment target: TBD  

This version is a production-ready MVP with PostgreSQL from the start.

---

## 2. Architecture

Mobile App (Expo)
        ↓
FastAPI Backend
        ↓
Scheduler + Scraper
        ↓
PostgreSQL

---

## 3. Tech Stack

### Frontend
- Expo
- Expo Push Notifications

### Backend
- FastAPI
- Uvicorn (ASGI)
- BeautifulSoup4
- Requests
- APScheduler
- SQLAlchemy 2.x (async)
- asyncpg
- PostgreSQL
- hashlib

### Environment
- uv (Python virtual environment manager)
- Docker support

---

## 4. Functional Scope (MVP)

### 4.1 Monitoring Target

- Single predefined URL
- Single predefined CSS selector
- Configurable via environment variables

Example:

MONITOR_URL=https://www.tokyodisneyresort.jp/tdr/news/update/  
MONITOR_SELECTOR=.linkList6.listUpdate ul

---

### 4.2 Monitoring Logic

1. Fetch page
2. Extract section via CSS selector
3. Convert to plain text
4. Generate SHA256 hash
5. Compare with stored hash
6. If changed:
   - Update hash
   - Store last_updated_at
   - Send push notification

---

### 4.3 Monitoring Interval

- Default: every 60 minutes
- Random delay (0–30 seconds)
- Run once on server startup

---

### 4.4 Push Notification Format

Title:
✨ TDRサイト更新情報が更新されました

Body:
東京ディズニーリゾート公式サイトの更新情報を確認してください。

---

## 5. API Endpoints

### POST /register

Registers Expo push token.

Request:
{
  "push_token": "ExponentPushToken[...]"
}

Response:
{
  "status": "registered"
}

---

### GET /status

Returns monitoring status.

Response:
{
  "last_checked_at": "...",
  "last_updated_at": "..."
}

---

## 6. Database Design (PostgreSQL)

### users

| Field        | Type        |
|-------------|------------|
| id          | UUID       |
| push_token  | TEXT       |
| created_at  | TIMESTAMP  |

---

### monitor_state

| Field            | Type        |
|------------------|------------|
| id               | UUID       |
| url              | TEXT       |
| selector         | TEXT       |
| last_hash        | TEXT       |
| last_checked_at  | TIMESTAMP  |
| last_updated_at  | TIMESTAMP  |

Note:
Only one row exists in MVP.

---

## 7. Security & Compliance

- robots.txt verification required
- Monitoring interval ≥ 1 hour
- Custom User-Agent defined
- 5-second timeout
- Stop after 3 consecutive failures
- No redistribution of scraped data

---

## 8. Project Structure

backend/
 ├── main.py
 ├── database.py
 ├── models.py
 ├── scraper.py
 ├── scheduler.py
 ├── notifier.py
 ├── config.py
 ├── requirements.txt
 └── Dockerfile

---

## 9. Environment Setup (uv)

Create virtual environment:

uv venv

Activate:

source .venv/bin/activate

Install dependencies:

uv pip install -r requirements.txt

Run locally:

uvicorn main:app --reload

---

## 10. Environment Variables

DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db  
MONITOR_URL=https://...  
MONITOR_SELECTOR=.linkList6.listUpdate ul  
CHECK_INTERVAL_MINUTES=60  
USER_AGENT=DisneyMonitorBot/1.0  

---

## 11. Docker Support

The backend must support containerized deployment.

### Dockerfile (PostgreSQL-ready)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY requirements.txt ./
RUN uv venv
RUN . .venv/bin/activate && uv pip install -r requirements.txt
COPY . .

EXPOSE 8000

CMD [".venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

```

---

# 🔥 今の設計状態

✔ PostgreSQL前提  
✔ async対応前提  
✔ uv採用  
✔ Docker正式仕様入り  
✔ 単一URL監視  
✔ 認証なし  

---
