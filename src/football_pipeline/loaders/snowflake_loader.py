"""Loads validated payloads into the RAW schema in Snowflake."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import snowflake.connector
import structlog
from cryptography.hazmat.primitives import serialization

from football_pipeline.config.settings import Settings

logger = structlog.get_logger(__name__)

_PEM_PATTERN = re.compile(
    r"-----BEGIN (?P<label>[A-Z ]+)-----(?P<body>.*?)-----END (?P=label)-----",
    re.DOTALL,
)


def _normalize_pem(raw: str) -> bytes:
    """Rebuilds a well-formed PEM regardless of how its whitespace got
    mangled in transit (a single-line env var field, a literal "\\n" text
    sequence instead of a real newline, etc.) - common when a multi-line
    secret is pasted into a host's env var UI rather than written to a
    file. Reconstructs standard 64-char-wrapped PEM from just the
    BEGIN/END markers and the base64 payload between them.
    """
    match = _PEM_PATTERN.search(raw)
    if not match:
        raise ValueError(
            "SNOWFLAKE_PRIVATE_KEY does not contain a recognizable "
            "-----BEGIN/END ... KEY----- block"
        )
    label = match.group("label")
    body = match.group("body").replace("\\n", "\n")
    body = re.sub(r"\s+", "", body)
    wrapped = "\n".join(body[i : i + 64] for i in range(0, len(body), 64))
    return f"-----BEGIN {label}-----\n{wrapped}\n-----END {label}-----\n".encode()


def _private_key_der_from_pem(pem_bytes: bytes, passphrase: str) -> bytes:
    normalized = _normalize_pem(pem_bytes.decode())
    private_key = serialization.load_pem_private_key(
        normalized, password=passphrase.encode() if passphrase else None
    )
    return private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


def connect(settings: Settings) -> snowflake.connector.SnowflakeConnection:
    """Key-pair auth is preferred: it doesn't trigger interactive MFA, so it
    works for non-interactive callers (this pipeline, the dashboard API,
    CI). Falls back to password auth, which on an MFA-enforced account will
    prompt for/require Duo approval.

    Two ways to supply the key, for different hosting environments:
    - SNOWFLAKE_PRIVATE_KEY_PATH: a file path (local dev, CI - where a
      secret can be written to disk before the process starts).
    - SNOWFLAKE_PRIVATE_KEY: the PEM content itself, for hosts where env
      vars are the only secret mechanism (e.g. Render, which doesn't
      support a "secret file" on its web service plan).
    """
    passphrase = settings.snowflake_private_key_passphrase
    private_key_der: bytes | None = None

    if settings.snowflake_private_key_path:
        private_key_der = _private_key_der_from_pem(
            Path(settings.snowflake_private_key_path).read_bytes(), passphrase
        )
    elif settings.snowflake_private_key:
        private_key_der = _private_key_der_from_pem(
            settings.snowflake_private_key.encode(), passphrase
        )

    if private_key_der is not None:
        return snowflake.connector.connect(
            account=settings.snowflake_account,
            user=settings.snowflake_user,
            private_key=private_key_der,
            role=settings.snowflake_role,
            warehouse=settings.snowflake_warehouse,
            database=settings.snowflake_database,
            schema="RAW",
        )

    return snowflake.connector.connect(
        account=settings.snowflake_account,
        user=settings.snowflake_user,
        password=settings.snowflake_password,
        role=settings.snowflake_role,
        warehouse=settings.snowflake_warehouse,
        database=settings.snowflake_database,
        schema="RAW",
    )


class SnowflakeLoader:
    """Writes raw entity payloads to RAW.* tables. One row per entity per load."""

    def __init__(self, conn: snowflake.connector.SnowflakeConnection) -> None:
        self._conn = conn

    def load_competition(
        self, competition_code: str, run_id: str, source: str, payload: dict[str, Any]
    ) -> int:
        return self._insert_one(
            table="RAW_COMPETITIONS",
            columns=["competition_code", "run_id", "source", "loaded_at", "raw_json"],
            row=(competition_code, run_id, source, _now(), json.dumps(payload)),
        )

    def load_teams(
        self,
        competition_code: str,
        season: str | None,
        run_id: str,
        source: str,
        teams: list[dict[str, Any]],
    ) -> int:
        loaded_at = _now()
        rows = [
            (competition_code, season, run_id, source, loaded_at, json.dumps(team))
            for team in teams
        ]
        return self._insert_many(
            table="RAW_TEAMS",
            columns=["competition_code", "season", "run_id", "source", "loaded_at", "raw_json"],
            rows=rows,
        )

    def load_matches(
        self,
        competition_code: str,
        season: str,
        run_id: str,
        source: str,
        matches: list[dict[str, Any]],
    ) -> int:
        loaded_at = _now()
        rows = [
            (
                competition_code,
                season,
                str(match.get("matchday", "")) or None,
                str(match["id"]),
                run_id,
                source,
                loaded_at,
                json.dumps(match),
            )
            for match in matches
        ]
        return self._insert_many(
            table="RAW_MATCHES",
            columns=[
                "competition_code",
                "season",
                "matchweek",
                "match_id",
                "run_id",
                "source",
                "loaded_at",
                "raw_json",
            ],
            rows=rows,
        )

    def load_standings(
        self,
        competition_code: str,
        season: str,
        run_id: str,
        source: str,
        payload: dict[str, Any],
    ) -> int:
        return self._insert_one(
            table="RAW_STANDINGS",
            columns=[
                "competition_code",
                "season",
                "snapshot_date",
                "run_id",
                "source",
                "loaded_at",
                "raw_json",
            ],
            row=(
                competition_code,
                season,
                datetime.now(UTC).date().isoformat(),
                run_id,
                source,
                _now(),
                json.dumps(payload),
            ),
        )

    # -- Internals -----------------------------------------------------

    def _insert_one(self, table: str, columns: list[str], row: tuple) -> int:
        return self._insert_many(table, columns, [row])

    def _insert_many(self, table: str, columns: list[str], rows: list[tuple]) -> int:
        if not rows:
            logger.info("snowflake_load_skipped_empty", table=table)
            return 0

        variant_index = columns.index("raw_json")
        placeholders = [
            "PARSE_JSON(%s)" if i == variant_index else "%s" for i in range(len(columns))
        ]
        sql = (
            f"INSERT INTO {table} ({', '.join(columns)}) "
            f"SELECT {', '.join(placeholders)}"
        )
        # Snowflake's executemany with PARSE_JSON needs one execute per row
        # (bulk paramstyle rewriting doesn't play well with function calls in VALUES).
        cursor = self._conn.cursor()
        try:
            for row in rows:
                cursor.execute(sql, row)
        finally:
            cursor.close()

        logger.info("snowflake_load_complete", table=table, row_count=len(rows))
        return len(rows)


def _now() -> str:
    return datetime.now(UTC).isoformat()
