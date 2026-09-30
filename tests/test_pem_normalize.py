import pytest

from football_pipeline.loaders.snowflake_loader import _normalize_pem

_BODY_LINES = ["A" * 64, "B" * 64, "C" * 10]
_WELL_FORMED = (
    "-----BEGIN PRIVATE KEY-----\n" + "\n".join(_BODY_LINES) + "\n-----END PRIVATE KEY-----\n"
)
_EXPECTED_BODY = "".join(_BODY_LINES)


def _rewrapped_body(pem_bytes: bytes) -> str:
    text = pem_bytes.decode()
    lines = text.strip().splitlines()
    return "".join(lines[1:-1])


def test_well_formed_pem_round_trips() -> None:
    result = _normalize_pem(_WELL_FORMED)
    assert _rewrapped_body(result) == _EXPECTED_BODY
    assert result.startswith(b"-----BEGIN PRIVATE KEY-----")
    assert result.rstrip(b"\n").endswith(b"-----END PRIVATE KEY-----")


def test_literal_backslash_n_is_normalized() -> None:
    mangled = _WELL_FORMED.replace("\n", "\\n")
    result = _normalize_pem(mangled)
    assert _rewrapped_body(result) == _EXPECTED_BODY


def test_newlines_collapsed_to_spaces_is_normalized() -> None:
    mangled = _WELL_FORMED.replace("\n", " ")
    result = _normalize_pem(mangled)
    assert _rewrapped_body(result) == _EXPECTED_BODY


def test_newlines_stripped_entirely_is_normalized() -> None:
    mangled = _WELL_FORMED.replace("\n", "")
    result = _normalize_pem(mangled)
    assert _rewrapped_body(result) == _EXPECTED_BODY


def test_missing_markers_raises_clear_error() -> None:
    with pytest.raises(ValueError, match="BEGIN/END"):
        _normalize_pem("not a pem at all")
