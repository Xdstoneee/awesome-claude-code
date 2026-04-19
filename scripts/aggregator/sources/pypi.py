"""PyPI source — download stats for Claude Code Python packages."""

from __future__ import annotations

import sys
from datetime import datetime

import requests

from scripts.aggregator.models import SourceResult, SourceType

_PYPI_STATS_URL = "https://pypistats.org/api/packages/{package}/recent"
_PYPI_SEARCH_URL = "https://pypi.org/pypi/{package}/json"
_PYPI_SIMPLE_SEARCH = "https://pypi.org/search/"
_TIMEOUT = 20

# Seed list of known Claude Code Python packages; augmented by search results
_SEED_PACKAGES = [
    "claude-code",
    "anthropic",
    "claude-code-sdk",
]

_SEARCH_TERMS = ["claude-code", "anthropic-claude"]


def _fetch_pypi_metadata(package: str) -> dict[str, object] | None:
    """Check if a package exists on PyPI and return basic metadata."""
    try:
        resp = requests.get(_PYPI_SEARCH_URL.format(package=package), timeout=_TIMEOUT)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        info = resp.json().get("info", {})
        return {
            "package": package,
            "version": info.get("version", ""),
            "summary": info.get("summary", ""),
            "home_page": info.get("home_page", "") or info.get("project_url", ""),
        }
    except requests.RequestException:
        return None


def _fetch_downloads(package: str) -> dict[str, object] | None:
    """Fetch recent download stats from pypistats.org."""
    try:
        resp = requests.get(
            _PYPI_STATS_URL.format(package=package),
            headers={"Accept": "application/json"},
            timeout=_TIMEOUT,
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json().get("data", {})
        return {
            "downloads_last_day": data.get("last_day", 0),
            "downloads_last_week": data.get("last_week", 0),
            "downloads_last_month": data.get("last_month", 0),
        }
    except requests.RequestException as e:
        print(f"  ✗ PyPI stats error for '{package}': {e}", file=sys.stderr)
        return None


def fetch(extra_packages: list[str] | None = None) -> SourceResult:
    """Fetch PyPI download stats for claude-code-related packages."""
    fetched_at = datetime.utcnow()
    errors: list[str] = []

    candidate_packages = list(_SEED_PACKAGES) + (extra_packages or [])
    seen: set[str] = set()
    unique = [p for p in candidate_packages if not (p in seen or seen.add(p))]  # type: ignore[func-returns-value]

    records: list[dict[str, object]] = []
    for pkg in unique:
        meta = _fetch_pypi_metadata(pkg)
        if not meta:
            continue
        stats = _fetch_downloads(pkg)
        if stats:
            records.append({**meta, **stats})
        else:
            errors.append(f"No download stats for PyPI package: {pkg}")

    print(f"  ✓ PyPI: {len(records)} packages fetched")
    return SourceResult(source=SourceType.PYPI, fetched_at=fetched_at, records=records, errors=errors)
