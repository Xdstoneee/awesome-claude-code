"""npm Registry source — download stats for Claude Code JS/TS packages."""

from __future__ import annotations

import sys
from datetime import datetime

import requests

from scripts.aggregator.models import SourceResult, SourceType

_NPM_DOWNLOADS_URL = "https://api.npmjs.org/downloads/point/last-month/{package}"
_NPM_SEARCH_URL = "https://registry.npmjs.org/-/v1/search"
_SEARCH_TERMS = ["claude-code", "claude code", "anthropic claude"]
_TIMEOUT = 20


def _search_packages(term: str) -> list[str]:
    try:
        resp = requests.get(
            _NPM_SEARCH_URL,
            params={"text": term, "size": 50},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        return [obj["package"]["name"] for obj in resp.json().get("objects", [])]
    except requests.RequestException as e:
        print(f"  ✗ npm search error for '{term}': {e}", file=sys.stderr)
        return []


def _fetch_downloads(package: str) -> dict[str, object] | None:
    try:
        resp = requests.get(
            _NPM_DOWNLOADS_URL.format(package=requests.utils.quote(package, safe="")),
            timeout=_TIMEOUT,
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()
        return {
            "package": package,
            "downloads_last_month": data.get("downloads", 0),
            "start": data.get("start", ""),
            "end": data.get("end", ""),
        }
    except requests.RequestException as e:
        print(f"  ✗ npm downloads error for '{package}': {e}", file=sys.stderr)
        return None


def fetch(extra_packages: list[str] | None = None) -> SourceResult:
    """Fetch npm download stats for claude-code-related packages."""
    fetched_at = datetime.utcnow()
    errors: list[str] = []

    # Discover packages via npm search
    seen: set[str] = set()
    packages: list[str] = list(extra_packages or [])
    for term in _SEARCH_TERMS:
        for pkg in _search_packages(term):
            if pkg not in seen:
                seen.add(pkg)
                packages.append(pkg)

    # Deduplicate while preserving order
    unique: list[str] = []
    final_seen: set[str] = set()
    for p in packages:
        if p not in final_seen:
            final_seen.add(p)
            unique.append(p)

    records: list[dict[str, object]] = []
    for pkg in unique:
        result = _fetch_downloads(pkg)
        if result:
            records.append(result)
        else:
            errors.append(f"No data for npm package: {pkg}")

    print(f"  ✓ npm: {len(records)} packages fetched")
    return SourceResult(source=SourceType.NPM, fetched_at=fetched_at, records=records, errors=errors)
