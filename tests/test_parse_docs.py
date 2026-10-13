"""The parser names columns. It does not exit, and loopstats is not sysstats."""

from __future__ import annotations

from ntpxyz import parse


def test_the_parser_does_not_claim_to_exit() -> None:
    assert "Exit if an error" not in (parse.__doc__ or "")


def test_parse_loopstats_does_not_claim_a_sysstats_refusal() -> None:
    assert "AmbiguousLayout" not in (parse.parse_loopstats.__doc__ or "")
