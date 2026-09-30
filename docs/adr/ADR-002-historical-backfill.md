# ADR-002: Historical Backfill Scope

## Context

Phase 0 research (generic third-party API documentation) suggested
football-data.org's free tier covered a large historical range. This was
never verified against a real API key before backfill was first attempted.

## What actually happened

Running `python -m football_pipeline --mode backfill --start-season 2018`
failed immediately with `403 Forbidden` on the `teams` endpoint for season
2018. Testing directly against a real free-tier key showed:

- Seasons **2023/24 through the current season** return data successfully.
- Season **2022/23 and earlier** return 403: *"The resource you are looking
  for is restricted and apparently not within your permissions."*

## Decision

**Backfill scope is 2023/24 onward** - the last ~4 seasons, which is what
the free tier actually exposes. `--start-season 2023` is the practical
floor for this data source; attempting anything earlier will fail loudly
(and did, visibly, in `AUDIT.PIPELINE_RUN_AUDIT`) rather than being
silently skipped.

## Consequences

- The MVP's historical depth is materially smaller than originally scoped.
  This is documented plainly in [docs/data_sources.md](../data_sources.md)
  rather than left as a stale claim from before it was tested.
- Deeper history would require a paid football-data.org subscription (not
  pursued, to keep the project at $0 cost) or a different/additional source
  - out of scope unless revisited later.
- This is a concrete example of the project's stated principle: verify
  data-source claims against a real key before building on them, and
  correct the record when a research-stage assumption turns out wrong.
