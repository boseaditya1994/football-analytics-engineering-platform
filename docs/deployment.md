# Deployment

The dashboard is two separately-deployed pieces: the FastAPI backend
(needs a live Snowflake connection, so it can't be static) and the React
frontend (static, built by Vite).

**Live**: backend at
[football-analytics-api-qcpm.onrender.com](https://football-analytics-api-qcpm.onrender.com),
frontend at
[football-analytics-engineering-plat.vercel.app](https://football-analytics-engineering-plat.vercel.app) -
both verified end-to-end (all four dashboard pages, including direct deep
links, plus the API's raw JSON responses).

## What actually went wrong getting here

Documented because every one of these was a real deploy failure, not a
hypothetical - useful if this ever needs debugging again, or redeploying
from scratch:

1. **`render.yaml`'s original `secretFiles` field isn't real** - Render's
   Blueprint schema rejected it outright (`field secretFiles not found in
   type file.Service`) before the service ever started, since Render web
   services have no mountable secret file. Fixed by adding
   `SNOWFLAKE_PRIVATE_KEY` as a second, env-var-based way to supply the
   key (`src/football_pipeline/loaders/snowflake_loader.py`), alongside
   the file-path version used locally and in CI.
2. **The pasted PEM lost its line breaks** - Render's env var field
   collapsed the multi-line key into something `cryptography` couldn't
   parse (`MalformedFraming`). Fixed by normalizing whatever whitespace
   survived the paste (`_normalize_pem()`) rather than depending on the
   paste being exact - verified against several realistic mangled forms,
   not just the one that happened (see `tests/test_pem_normalize.py`).
3. **First paste attempt only captured one line** - a second, genuinely
   different failure from #2: the BEGIN/END markers were missing
   entirely, meaning the paste itself was incomplete. No code fix for
   this one - just re-copying the full file content and re-pasting
   carefully into Render's editable field.
4. **`VITE_API_BASE_URL` was missing its `https://` scheme** and was set
   to Vercel's "Secret" type, which - per Vercel's own UI warning - can't
   be safely used for a `VITE_`-prefixed variable (those are compiled
   into the public bundle regardless, so "Secret" doesn't add protection
   and apparently isn't available at build time the same way "Config"
   is). Vercel doesn't allow converting a saved Secret to Config in
   place; had to delete and re-add the variable as Config.
5. **Direct navigation to any route other than `/` 404'd** on the
   deployed frontend (e.g. `/pipeline`) even though in-app navigation
   worked fine. Vercel's static file server has no `index.html` to serve
   for a path it doesn't recognize; client-side routes only exist once
   `index.html` has loaded and react-router takes over. Fixed with
   `dashboards/react/vercel.json`'s catch-all rewrite to `/index.html`.

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
   - `SNOWFLAKE_PRIVATE_KEY` — paste the **full contents** of your local `.snowflake_keys/rsa_key.p8` (the private key file, including the `-----BEGIN PRIVATE KEY-----`/`-----END PRIVATE KEY-----` lines) directly into this env var's value field. Render's env var editor accepts multi-line values.
     (Render web services don't support a mountable "secret file," unlike GitHub Actions - this project's `connect()` function supports both a file path, for local dev/CI, and this raw-content env var, for hosts like Render. Verified working both ways.)
   - `ALLOWED_ORIGINS` — leave blank for now, or set to `*` temporarily; you'll set it to your real Vercel URL after deploying the frontend (see below). `ALLOWED_ORIGIN_REGEX` is already set in `render.yaml` to allow any `*.vercel.app` domain, so this is a convenience, not a requirement.
4. Deploy. Render will run `pip install -e ".[dashboard]"` then start `uvicorn`.
5. Once live, note the service URL (something like `https://football-analytics-api-qcpm.onrender.com`) — the frontend needs it.

**Free tier note**: Render's free web services spin down after 15 minutes
of inactivity and take ~30-60s to wake on the next request. Document this
rather than being surprised by it - it's not a bug.

## Frontend — Vercel (free tier)

1. Sign in to [Vercel](https://vercel.com) with your GitHub account.
2. **Add New** → **Project** → import the same repo.
3. Set **Root Directory** to `dashboards/react`. Vercel auto-detects Vite - no other config needed.
4. Add an environment variable: `VITE_API_BASE_URL` = the Render backend URL from above (no trailing slash), e.g. `https://football-analytics-api-qcpm.onrender.com`.
5. Deploy. Vercel gives you a URL like `https://football-analytics-engineering-plat.vercel.app`.

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
