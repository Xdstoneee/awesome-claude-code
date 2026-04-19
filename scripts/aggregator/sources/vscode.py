"""VS Code Marketplace source — install counts and ratings for Claude Code extensions.

Uses the public VS Code Marketplace REST API (no auth required).
"""

from __future__ import annotations

import sys
from datetime import datetime

import requests

from scripts.aggregator.models import SourceResult, SourceType

_MARKETPLACE_API = "https://marketplace.visualstudio.com/_apis/public/gallery/extensionquery"
_TIMEOUT = 30
_API_VERSION = "7.2-preview.1"

# Search criteria flags per the VS Code Gallery API spec
_FILTER_TYPE_SEARCH_TEXT = 10
_SORT_BY_INSTALL_COUNT = 4

_SEARCH_TERMS = ["claude code", "claude-code", "anthropic claude"]


def _query_marketplace(search_text: str, page_size: int = 50) -> list[dict[str, object]]:
    payload = {
        "filters": [
            {
                "criteria": [
                    {"filterType": _FILTER_TYPE_SEARCH_TEXT, "value": search_text},
                ],
                "pageSize": page_size,
                "pageNumber": 1,
                "sortBy": _SORT_BY_INSTALL_COUNT,
            }
        ],
        "flags": 914,  # include statistics, versions, tags, publisher
    }
    headers = {
        "Accept": f"application/json;api-version={_API_VERSION}",
        "Content-Type": "application/json",
    }
    try:
        resp = requests.post(_MARKETPLACE_API, json=payload, headers=headers, timeout=_TIMEOUT)
        resp.raise_for_status()
        results = resp.json().get("results", [])
        if not results:
            return []
        return results[0].get("extensions", [])
    except requests.RequestException as e:
        print(f"  ✗ VS Code Marketplace error for '{search_text}': {e}", file=sys.stderr)
        return []


def _extract_stat(stats: list[dict[str, object]], stat_name: str) -> int:
    for s in stats:
        if s.get("statisticName") == stat_name:
            return int(s.get("value", 0))
    return 0


def fetch() -> SourceResult:
    """Fetch VS Code extension data for Claude Code extensions."""
    fetched_at = datetime.utcnow()

    seen_ids: set[str] = set()
    records: list[dict[str, object]] = []

    for term in _SEARCH_TERMS:
        for ext in _query_marketplace(term):
            ext_id = ext.get("extensionId", "")
            if ext_id in seen_ids:
                continue
            seen_ids.add(str(ext_id))

            publisher = ext.get("publisher", {})
            stats: list[dict[str, object]] = ext.get("statistics", [])  # type: ignore[assignment]

            records.append({
                "extension_id": ext_id,
                "name": ext.get("extensionName", ""),
                "display_name": ext.get("displayName", ""),
                "publisher": publisher.get("publisherName", ""),
                "short_description": ext.get("shortDescription", ""),
                "install_count": _extract_stat(stats, "install"),
                "rating": _extract_stat(stats, "averagerating"),
                "rating_count": _extract_stat(stats, "ratingcount"),
                "last_updated": ext.get("lastUpdated", ""),
                "marketplace_url": (
                    f"https://marketplace.visualstudio.com/items?itemName="
                    f"{publisher.get('publisherName', '')}.{ext.get('extensionName', '')}"
                ),
                "search_term": term,
            })

    print(f"  ✓ VS Code Marketplace: {len(records)} extensions fetched")
    return SourceResult(source=SourceType.VSCODE, fetched_at=fetched_at, records=records)
