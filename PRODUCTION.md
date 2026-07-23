# KrishiIQ — Production Deployment Guide

## Architecture

| Component | Users | URL |
|-----------|-------|-----|
| **Mobile app** (Flutter) | Farmers | Android/iOS |
| **Web dashboard** (React) | Officers, Admins | `https://your-domain.com` |
| **API** (FastAPI) | Both | `https://api.your-domain.com` |

## Role-based access

| Role | Mobile app | Web dashboard |
|------|------------|---------------|
| `farmer` | Yes | Blocked |
| `officer` | Blocked | Yes |
| `admin` | Blocked | Yes |

## Environment variables

### Backend (`backend/.env.local`)

```env
DATABASE_URL=postgresql://user:pass@host:5432/krishiiq_db
REDIS_URL=redis://host:6379/0
SECRET_KEY=<long-random-secret>
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
GOOGLE_MAPS_API_KEY=AIza...
OPENWEATHER_API_KEY=...
ENVIRONMENT=production
CORS_ORIGINS=https://dashboard.your-domain.com
```

### Web (`web-dashboard/.env.local`)

```env
VITE_GOOGLE_MAPS_API_KEY=AIza...
```

### Mobile (`lib/config/app_config.dart`)

Set `baseUrl` to your production API, e.g. `https://api.your-domain.com/api/v1`.

## Production checklist

- [ ] Rotate all API keys; never commit `.env.local`
- [ ] Set `ENVIRONMENT=production`
- [ ] Restrict Google Maps API key by HTTP referrer / app package
- [ ] Use HTTPS everywhere
- [ ] Run `python seed.py` only on empty DB (or remove demo accounts)
- [ ] Configure PostgreSQL backups
- [ ] Add rate limiting on `/auth/register` and `/ai/chat`

## Quick start (development)

```powershell
# Backend
cd backend
pip install -r requirements.txt
copy .env.local.example .env.local
# Edit .env.local with your keys
python seed.py
uvicorn app.main:app --reload

# Web
cd web-dashboard
npm install
copy .env.example .env.local
npm run dev

# Mobile
cd mobile
flutter pub get
flutter run
```

## Test accounts (after seed)

| Role | Phone | Password |
|------|-------|----------|
| Farmer | 9000000002 | farmer123 |
| Officer | 9000000001 | officer123 |
| Admin | 9000000003 | admin123 |


## Mobile app flow (per spec document)

1. Welcome → Register or Sign In  
2. Register → Farm setup → Main app  
3. Bottom nav: Home · Advisory · Sensors · History · Profile  
4. AI chat, disease detection, voice advisories, offline advisory cache  

## API docs

With backend running: http://localhost:8000/docs
