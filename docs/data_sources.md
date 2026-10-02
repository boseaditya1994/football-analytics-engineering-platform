# Data Sources

## Primary: football-data.org

| | |
|---|---|
| Provider | [football-data.org](https://www.football-data.org/) |
| Purpose | Core competition/team/match/standings data |
| Datasets used | Competitions, Teams, Matches, Standings |
| Granularity | Match-level results and status, season standings snapshots |
| Update frequency | Ingested daily for the current season via the pipeline's `--mode daily`; football-data.org itself updates match status/scores continuously, delayed on the free tier |
| Free tier rate limit | 10 requests/minute (enforced client-side, see [`rate_limiter.py`](../src/football_pipeline/api/rate_limiter.py)) |
| Licensing | Personal/non-commercial API use per football-data.org's terms |

### Historical coverage — corrected from initial assumption

Phase 0's initial research (based on generic third-party documentation, not a
direct test against a real API key) assumed decades of historical Premier
League coverage was available on the free tier. **That assumption was wrong.**

Testing directly against a real free-tier API key on 2026-09-29 showed:

- Seasons **2023/24 through 2026/27** (`season=2023` through `season=2026`)
  return data successfully.
- Season **2022/23 and earlier** (`season=2022` and older) return
  `403 Forbidden`: *"The resource you are looking for is restricted and
  apparently not within your permissions. Please check your subscription."*

**Corrected scope: the free tier exposes only the last ~4 seasons.** This is
a hard constraint of the data source, not a bug in the pipeline. The initial
backfill was run with `--start-season 2023` for this reason — attempting
`--start-season 2018` was tried first and failed exactly as described above
(see `AUDIT.PIPELINE_RUN_AUDIT` for the failed run).

**Implication for this project:** the MVP's historical depth is
2023/24–present, not "multiple decades" as originally scoped. Deeper
historical seasons would require a paid football-data.org subscription (not
pursued, to keep the project at $0 cost) or a different data source
(e.g. an open historical dataset), which is out of scope unless revisited
later.

### Response shape notes (discovered by testing, not assumed)

- `/teams` and `/standings` responses include a top-level `count` field;
  `/matches` does **not**. The API client's response-envelope validation
  ([`schemas.py`](../src/football_pipeline/api/schemas.py)) reflects the
  actual shapes, verified against live responses.
- Rate limiting is enforced **per-process**
  ([`rate_limiter.py`](../src/football_pipeline/api/rate_limiter.py)), not
  globally across separate invocations. Running several short-lived
  `python -c "..."` feasibility checks immediately before a `--mode
  backfill` run (each starting a fresh, empty rate-limiter) caused a real
  429 even though each individual process respected 10 req/min - the
  combined request rate across processes didn't. The existing retry/backoff
  handled it on the next invocation; a shared/persistent rate limiter would
  be the real fix if this becomes a recurring problem, not implemented
  since it's only ever bitten manual/interactive use, never the scheduled
  pipeline (which runs as a single process).

## Competitions ingested

Multiple competitions on the free tier have been verified and ingested -
not just assumed available because they're "one of the 12":

| Competition | Code | Type | Seasons | Teams/season | Format notes |
|---|---|---|---|---|---|
| Premier League | `PL` | League | 2023/24-2026/27 | 20 | Standard single round-robin |
| UEFA Champions League | `CL` | Cup | 2023/24-2026/27 | 32 (2023/24), 36 (2024/25+) | Group stage (pre-2024) / league phase (2024/25+) plus knockout rounds - see [ADR-011](adr/ADR-011-standings-scope-and-multi-competition.md) for how standings are scoped to the table-eligible portion only |
| Eredivisie | `DED` | League | 2023/24-2026/27 | 18 | Standard single round-robin |
| Bundesliga | `BL1` | League | 2023/24-2026/27 | 18 | Standard single round-robin; surfaced a real `AWARDED`-match handling gap - see [ADR-011](adr/ADR-011-standings-scope-and-multi-competition.md) |

Adding Eredivisie and Bundesliga required **zero code or schema changes**
beyond running the backfill CLI - a real test that the `competition_code`
grain fix (added for Champions League) actually generalizes, not just a
two-competition special case. The dashboard's competition picker is
populated dynamically from `/api/competitions`, so a newly-ingested
competition appears automatically.

## Deferred / not used in MVP

- **API-Football (api-sports.io)** — free tier capped at ~100 requests/day,
  too restrictive to justify as a second source for this project's scale.
- **StatsBomb Open Data** — event-level data with genuine xG, but only for
  specific individually-released seasons (not continuous coverage). Deferred
  to an optional future stretch goal, scoped separately from the core
  season-by-season fact tables if ever added.

## Disclaimer

This is an independent portfolio/educational analytics engineering project
and is not affiliated with, endorsed by, or sponsored by the Premier League,
any other football competition, or their clubs. Data attribution and usage
are subject to football-data.org's terms of use.
