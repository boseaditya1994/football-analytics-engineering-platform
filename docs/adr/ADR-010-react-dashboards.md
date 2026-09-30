# ADR-010: BI Choice - React Dashboard over Power BI/Tableau

## Context

The project needed a BI/presentation layer over the Snowflake marts. The
brief explicitly asked for "React Dashboards" as the chosen BI approach
rather than a conventional BI tool.

## Options

1. **Power BI / Tableau / Looker Studio** - fast to build, familiar BI
   tooling, but licensing/hosting friction for a public portfolio project
   (Power BI Desktop reports aren't natively web-embeddable without a paid
   Pro/Embedded tier; Tableau Public strips data-source connectivity).
2. **Streamlit** - fast Python-only iteration, but explicitly scoped as a
   stretch goal, not the primary BI layer, per the project brief.
3. **Custom React app + a thin backend** - full control over UX (crests,
   form pills, an interactive Recharts progression chart), freely
   deployable, and directly demonstrates full-stack + API-design skill
   alongside the data engineering work, which is more representative of
   what "React Dashboards" as a named deliverable implies.

## Decision

**Option 3**: Vite + React + TypeScript + Recharts, backed by a small
read-only FastAPI service (`dashboards/api`) that queries the MARTS/AUDIT
schemas. The frontend never talks to Snowflake directly - credentials stay
server-side, the frontend only ever calls `/api/*`.

Four pages, each matched to a real mart grain rather than an arbitrary UI
idea: Overview (`mart_league_table`), Progression (`mart_league_progression`),
Team Compare (`mart_league_table` + `mart_home_away_performance` +
`mart_goal_analysis`), Pipeline Health (`AUDIT.PIPELINE_RUN_AUDIT` +
`AUDIT.DATA_QUALITY_AUDIT`) - the last one being the deliberate
data-engineering differentiator called for in the project brief, not just
another football stat page.

## Consequences

- No BI tool licensing or embedding constraints; deployable as a static
  site + a small API service anywhere.
- More implementation work than pointing a BI tool at Snowflake, but the
  dashboard now demonstrates API design (`dashboards/api/main.py`) and
  frontend engineering as well as analytics engineering - a broader skill
  showcase for the same project.
- **Refresh strategy**: on-demand - the dashboard always queries live
  Snowflake data through the API on every page load; there is no cached
  or pre-aggregated snapshot to go stale. "Automatic dashboard refresh" in
  the sense of a BI tool's scheduled extract doesn't apply here since
  there's no extract - this is documented explicitly to avoid overclaiming
  a refresh capability that isn't the actual architecture.
