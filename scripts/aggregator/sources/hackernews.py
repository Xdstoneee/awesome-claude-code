"""HackerNews source via the Algolia HN Search API (free, no auth)."""

from __future__ import annotations

import sys
from datetime import datetime

import requests

from scripts.aggregator.models import SourceResult, SourceType

_ALGOLIA_URL = "https://hn.algolia.com/api/v1/search"
_TIMEOUT = 20
_SEARCH_QUERIES = [
    "claude code",
    "claude-code anthropic",
    "Claude Code CLI",
]


def _search(query: str, tags: str = "story") -> list[dict[str, object]]:
    try:
        resp = requests.get(
            _ALGOLIA_URL,
            params={
                "query": query,
                "tags": tags,
                "hitsPerPage": 50,
                "attributesToRetrieve": "objectID,title,url,points,num_comments,created_at,author",
            },
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json().get("hits", [])
    except requests.RequestException as e:
        print(f"  ✗ HN search error for '{query}': {e}", file=sys.stderr)
        return []


def fetch() -> SourceResult:
    """Fetch HackerNews stories mentioning Claude Code."""
    fetched_at = datetime.utcnow()

    seen_ids: set[str] = set()
    records: list[dict[str, object]] = []

    for query in _SEARCH_QUERIES:
        for hit in _search(query):
            oid = str(hit.get("objectID", ""))
            if oid in seen_ids:
                continue
            seen_ids.add(oid)
            records.append({
                "id": oid,
                "title": hit.get("title", ""),
                "url": hit.get("url", ""),
                "hn_url": f"https://news.ycombinator.com/item?id={oid}",
                "points": hit.get("points", 0),
                "num_comments": hit.get("num_comments", 0),
                "author": hit.get("author", ""),
                "created_at": hit.get("created_at", ""),
                "search_query": query,
            })

    print(f"  ✓ HackerNews: {len(records)} stories fetched")
    return SourceResult(
        source=SourceType.HACKERNEWS,
        fetched_at=fetched_at,
        records=records,
    )
