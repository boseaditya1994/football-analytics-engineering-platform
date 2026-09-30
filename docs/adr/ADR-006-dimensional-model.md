# ADR-006: Dimensional Model Scope

## Context

football-data.org's free tier provides competition, team, match, and
standings data, but not player-level match statistics, event data, or
venue detail beyond a name string. The dimensional model needs to reflect
what's actually available, not a theoretical ideal schema.

## Decision

Dimensions: `dim_team`, `dim_season`, `dim_matchweek`, `dim_date`.
Facts: `fact_match`, `fact_team_match`, `fact_standing_snapshot`
(see [docs/data_model.md](../data_model.md) for grain/key documentation of
each).

**No `dim_player` or player-grain facts** - directly follows from
[ADR-001](ADR-001-data-source.md): the source doesn't provide reliable
player-level match stats, so building `fact_player_match` would mean
either leaving it permanently empty or building it on a source this
project doesn't actually have. Player analytics (dashboard page 6 in the
original project brief) is out of scope for the MVP as a direct
consequence, not an oversight.

**No `dim_venue`** - the source provides only a venue name string, not
structured venue data (capacity, location, surface). A dimension table for
a single un-normalized string column isn't justified; `venue_name` lives
directly on `dim_team`.

**No SCD Type 2 snapshots** - team metadata (name, crest, venue) changes
rarely enough in a single season's window that tracking historical
attribute changes wasn't worth the added complexity for this project's
scope. `dim_team` takes the most recent load per team. Revisit if a
genuine business need for point-in-time team attribute history emerges
(e.g. tracking a mid-season stadium change).

## Consequences

- The model is smaller than the original 18-phase project brief's full
  ambition, but every dimension and fact that exists is genuinely
  supported by real, verified data - nothing here is a stub table waiting
  for a data source that doesn't exist.
- Adding a second competition later doesn't require new dimensions - see
  [ADR-004](ADR-004-snowflake-architecture.md) for the `competition_code`
  design that makes this a data change, not a schema change.
