# linkedin-scraper-api

🚀 Real-Time LinkedIn Scraper API - Enhanced version with caching, rate limiting, retry logic and Prometheus monitoring. Built with FastAPI.

This service is a proxy/enrichment layer on top of the [linkedin-data-api](https://rapidapi.com/rockapis-rockapis-default/api/linkedin-data-api) on RapidAPI. **It does not work without a RapidAPI key.**

## Setup

1. **Get a RapidAPI key** — create an account on [rapidapi.com](https://rapidapi.com), subscribe to the `linkedin-data-api` (a free tier exists), and copy your `X-RapidAPI-Key`.

2. **Configure the environment:**

   ```bash
   cp .env.example .env
   # then edit .env and set LINKEDIN_RAPIDAPI_KEY=<your key>
   ```

3. **Install & run:**

   ```bash
   pip install -r requirements.txt
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

   Or with Docker:

   ```bash
   docker build -t linkedin-scraper-api .
   docker run -p 8000:8000 --env-file .env linkedin-scraper-api
   ```

4. **Verify:** open <http://localhost:8000/health> — `rapidapi_key_configured` must be `true`. Interactive docs are at <http://localhost:8000/docs>.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `rapidapi_key_configured: false` in `/health` | No `.env` file or empty key | Create `.env` from `.env.example` and set the key |
| HTTP 403 "Access denied by RapidAPI" | Invalid key, or not subscribed to the API | Check the key and your subscription on rapidapi.com |
| HTTP 429 | RapidAPI plan quota exceeded | Wait, or upgrade your plan |
| HTTP 503 "Request failed after N attempts" | Network cannot reach `linkedin-data-api.p.rapidapi.com` | Check firewall/proxy/DNS |

## Environment variables

All variables use the `LINKEDIN_` prefix (see `config.py`):

| Variable | Default | Description |
|---|---|---|
| `LINKEDIN_RAPIDAPI_KEY` | *(empty — required)* | Your RapidAPI key |
| `LINKEDIN_RAPIDAPI_HOST` | `linkedin-data-api.p.rapidapi.com` | Upstream host header |
| `LINKEDIN_BASE_URL` | `https://linkedin-data-api.p.rapidapi.com` | Upstream base URL |
| `LINKEDIN_CACHE_TTL` | `900` | Cache TTL in seconds |
| `LINKEDIN_RATE_LIMIT` | `100/minute` | Rate limit per client IP |
