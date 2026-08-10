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

## Switching the data provider

The upstream data source is pluggable behind a `LinkedInProvider` interface
(`services/providers/`), and routes return a **canonical** shape, so switching
providers is a config change — not a code change. The `/enrich/*` endpoints work
regardless of provider (they take caller-supplied data).

Select with `LINKEDIN_PROVIDER`:

| Value | Upstream | Cost | Set also |
|---|---|---|---|
| `pdl` | People Data Labs (Person Enrichment) | **Free** 100/mo | `LINKEDIN_PDL_API_KEY` (free, no card) |
| `rapidapi_generic` (default) | classic `linkedin-data-api`-style endpoints | varies | `LINKEDIN_RAPIDAPI_HOST`, `LINKEDIN_RAPIDAPI_KEY` |
| `fresh` | Fresh LinkedIn Profile Data (RapidAPI) | paid (~$10/mo) | host `fresh-linkedin-profile-data.p.rapidapi.com`, key |

**Recommended free start:** `pdl`. Get a free key at peopledatalabs.com (100
lookups/month, no card), set `LINKEDIN_PROVIDER=pdl` and `LINKEDIN_PDL_API_KEY`.
PDL returns licensed dataset records (name, title, experience, education, skills,
location) — reliable, but no follower counts or posts, so those enrichment
components degrade gracefully. Reselling raw PDL records needs a PDL license; the
free tier is for testing / your own use.

> The original `linkedin-data-api` (rockapis) was discontinued. To restore live
> data, subscribe to a working provider and point these vars at it. For a paid,
> resale product, prefer a **licensed** provider (Coresignal / People Data Labs)
> whose terms permit redistribution — reselling raw scraped LinkedIn data
> violates LinkedIn's ToS. Adding such a provider = one new class in
> `services/providers/` implementing `LinkedInProvider`.

> The `fresh` adapter maps fields defensively; confirm one real response against
> the Fresh playground and adjust the candidate keys in
> `services/providers/fresh.py` if any field comes back empty.

## Deploy on Render (GitHub → Render → RapidAPI)

This service is meant to be hosted (e.g. on Render) and then published as an API
on RapidAPI, which proxies requests to the hosted URL. Two things are essential:

1. **Bind `$PORT`.** Render injects a `PORT` env var and routes its health check
   to it. The Dockerfile already binds `${PORT:-8000}` — do not hardcode a port.
2. **Set the upstream key in Render, not `.env`.** `.env` is git-ignored and never
   deployed. In the Render service → **Environment**, add:
   - `LINKEDIN_RAPIDAPI_KEY` = your RapidAPI key (secret)
   - `LINKEDIN_RAPIDAPI_HOST` = `linkedin-data-api.p.rapidapi.com`

Set the Render **Health Check Path** to `/health`. After deploy, open
`https://<your-service>.onrender.com/health` and confirm
`"rapidapi_key_configured": true`.

> Note: on Render's free plan the service sleeps after inactivity; the first
> request cold-starts (~30–50s), which can make RapidAPI's first health probe
> time out. Retry, or use a paid plan to keep it warm.

When you publish this on RapidAPI, RapidAPI forwards requests to the Render URL
and adds an `X-RapidAPI-Proxy-Secret` header. Validating it is optional hardening,
not required for the API to function.

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
