"""Lightweight response-envelope validation for the football-data.org API.

These deliberately validate only the shape we depend on (top-level keys,
list-ness, presence of an id) — not every field. Full typing/renaming of
entity fields is dbt staging's job; RAW stores the untouched payload. This
layer exists to fail fast on a malformed or unexpected response rather than
silently loading garbage into RAW.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class _PermissiveModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class CompetitionEnvelope(_PermissiveModel):
    id: int
    code: str
    name: str


class TeamListEnvelope(_PermissiveModel):
    count: int
    teams: list[dict[str, Any]]


class MatchListEnvelope(_PermissiveModel):
    count: int
    matches: list[dict[str, Any]]


class StandingsEnvelope(_PermissiveModel):
    competition: dict[str, Any]
    season: dict[str, Any]
    standings: list[dict[str, Any]]
