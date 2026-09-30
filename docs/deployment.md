# Deployment

The dashboard is two separately-deployed pieces: the FastAPI backend
(needs a live Snowflake connection, so it can't be static) and the React
frontend (static, built by Vite).

## Backend — Render (free tier)

Config lives in `render.yaml` at the repo root (a Render "Blueprint" - lets
Render auto-configure the service from this file instead of clicking
through settings manually).

1. Sign in to [Render](https://render.com) with your GitHub account.
2. **New** → **Blueprint** → connect the `football-analytics-engineering-platform` repo. Render reads `render.yaml` and proposes one service: `football-analytics-api`.
3. Before/during creation, Render will prompt for the secrets marked `sync: false` in `render.yaml`:
   - `FOOTBALL_DATA_API_KEY`
   - `SNOWFLAKE_ACCOUNT`
   - `SNOWFLAKE_USER`
   - `ALLOWED_ORIGINS` — leave blank for now, or set to `*` temporarily; you'll set it to your real Vercel URL after deploying the frontend (see below). `ALLOWED_ORIGIN_REGEX` is already set in `render.yaml` to allow any `*.vercel.app` domain, so this is a convenience, not a requirement.
4. Also add a **Secret File**: name `rsa_key.p8`, contents = the full contents of your local `.snowflake_keys/rsa_key.p8` (the private key file). Render mounts it at `/etc/secrets/rsa_key.p8`, matching `SNOWFLAKE_PRIVATE_KEY_PATH` in `render.yaml`.
5. Deploy. Render will run `pip install -e ".[dashboard]"` then start `uvicorn`.
6. Once live, note the service URL (something like `https://football-analytics-api.onrender.com`) — the frontend needs it.

**Free tier note**: Render's free web services spin down after 15 minutes
of inactivity and take ~30-60s to wake on the next request. Document this
rather than being surprised by it - it's not a bug.

## Frontend — Vercel (free tier)

1. Sign in to [Vercel](https://vercel.com) with your GitHub account.
2. **Add New** → **Project** → import the same repo.
3. Set **Root Directory** to `dashboards/react`. Vercel auto-detects Vite - no other config needed.
4. Add an environment variable: `VITE_API_BASE_URL` = the Render backend URL from above (no trailing slash), e.g. `https://football-analytics-api.onrender.com`.
5. Deploy. Vercel gives you a URL like `https://football-analytics-engineering-platform.vercel.app`.

## Wiring CORS to the real frontend URL

Once you have the Vercel URL, either:
- Rely on `ALLOWED_ORIGIN_REGEX` (already set to accept any `*.vercel.app` domain - works out of the box, including preview deploys), or
- Set `ALLOWED_ORIGINS` on Render to the exact production URL for a tighter allowlist.

## Verifying it works

Open the Vercel URL. The Overview page should load a real league table. If
it doesn't:
- Check the Render service logs for a Snowflake connection error (most
  likely cause: the secret file or one of the sync:false env vars wasn't
  filled in correctly).
- Check the browser console for a CORS error (most likely cause: the
  Vercel URL isn't covered by `ALLOWED_ORIGINS`/`ALLOWED_ORIGIN_REGEX` yet).
