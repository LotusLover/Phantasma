#!/usr/bin/env python3
"""Offline, hypothetical token-cost calculator. Uses only the Python stdlib."""
from __future__ import annotations

import argparse
import json
import math
import sys
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path
from typing import Any


NOTICE = "HYPOTHETICAL FIXTURE: this is an offline estimate, not a measured charge."
RATE_KEYS = ("input", "cached_input", "output")


def _load_json(path: str | Path) -> dict[str, Any]:
    try:
        with Path(path).open("r", encoding="utf-8-sig") as stream:
            value = json.load(stream)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read JSON input: {path}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def _token_count(usage: dict[str, Any], name: str) -> int:
    value = usage.get(name)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer.")
    return value


def _rate(rates: dict[str, Any], name: str) -> Decimal:
    value = rates.get(name)
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise ValueError(f"{name} rate must be a finite non-negative number.")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"{name} rate must be a finite non-negative number.")
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{name} rate must be a finite non-negative number.") from None
    if not amount.is_finite() or amount < 0:
        raise ValueError(f"{name} rate must be a finite non-negative number.")
    return amount


def estimate_cost(usage: dict[str, Any], rates_usd_per_million: dict[str, Any]) -> dict[str, Any]:
    """Return an exact Decimal estimate from token counts and virtual rates."""
    if not isinstance(usage, dict) or not isinstance(rates_usd_per_million, dict):
        raise ValueError("usage and rates must both be JSON objects.")

    input_tokens = _token_count(usage, "input_tokens")
    cached_input_tokens = _token_count(usage, "cached_input_tokens")
    output_tokens = _token_count(usage, "output_tokens")
    if cached_input_tokens > input_tokens:
        raise ValueError("cached_input_tokens cannot exceed input_tokens.")

    rates = {key: _rate(rates_usd_per_million, key) for key in RATE_KEYS}
    uncached_input_tokens = input_tokens - cached_input_tokens
    with localcontext() as context:
        context.prec = 40
        million = Decimal(1_000_000)
        total = (
            Decimal(uncached_input_tokens) * rates["input"]
            + Decimal(cached_input_tokens) * rates["cached_input"]
            + Decimal(output_tokens) * rates["output"]
        ) / million

    return {
        "notice": NOTICE,
        "estimate_kind": "hypothetical_offline_estimate",
        "currency": "USD",
        "usage": {
            "input_tokens": input_tokens,
            "cached_input_tokens": cached_input_tokens,
            "output_tokens": output_tokens,
            "uncached_input_tokens": uncached_input_tokens,
        },
        "rates_usd_per_million_tokens": {key: format(rates[key], "f") for key in RATE_KEYS},
        "estimated_cost_usd": format(total, "f"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Estimate token cost from local JSON fixtures (hypothetical only).")
    parser.add_argument("usage_json", help="Path to usage JSON")
    parser.add_argument("rates_json", help="Path to virtual USD-per-million rates JSON")
    args = parser.parse_args(argv)
    try:
        usage = _load_json(args.usage_json)
        rates_file = _load_json(args.rates_json)
        rates = rates_file.get("rates_usd_per_million_tokens")
        result = estimate_cost(usage, rates)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
