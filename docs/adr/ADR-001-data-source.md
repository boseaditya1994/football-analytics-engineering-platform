# ADR-001: Primary EPL Data Source

## Context

The platform needs a legitimate, free, automatable source of Premier League
competition, team, match, and standings data, with clear licensing for a
public portfolio project.

## Options

1. **football-data.org (free tier)** - REST API, competitions/teams/matches/standings,
   10 req/min, personal/non-commercial use terms.
2. **API-Football (api-sports.io)** - richer per-match stats, but free tier
   capped at ~100 requests/day - too restrictive for backfill + daily ops
   without a paid key.
3. **StatsBomb Open Data** - genuine event-level data with real xG, but only
   for specific individually-released seasons (e.g. 2015/16), not
   continuous multi-season coverage.
4. **Scraping PremierLeague.com or similar** - rejected outright: violates
   the project's non-negotiable rule against scraping restricted sites.

## Decision

**football-data.org, free tier**, as the sole primary source for the MVP.
No secondary source - API-Football's free tier is too rate-capped to
justify the added architecture complexity, and StatsBomb's episodic
coverage doesn't fit the core season-by-season fact tables (deferred to an
optional, clearly-scoped stretch goal if ever added).

## Consequences

- Zero cost, sufficient rate limit for daily batch + backfill.
- **No player-level match stats** on the free tier (only top scorers) -
  player analytics dropped from MVP scope as a direct consequence.
- **No xG** - documented as out of scope, never approximated.
- Real, tested historical depth turned out to be only the last ~4 seasons,
  not the "decades" assumed from generic third-party docs during initial
  research - see [docs/data_sources.md](../data_sources.md) for the
  corrected finding and [ADR-002](ADR-002-historical-backfill.md) for how
  that changed the backfill scope.
