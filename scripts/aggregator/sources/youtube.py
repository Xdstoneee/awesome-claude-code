"""YouTube Data API v3 source — tutorial views for Claude Code content.

Free tier: 10,000 units/day. A search costs 100 units, so ~100 searches/day.
Get a key at console.cloud.google.com → YouTube Data API v3.
Set the YOUTUBE_API_KEY environment variable.

API docs: https://developers.google.com/youtube/v3/docs/search/list
"""

from __future__ import annotations

import os
import sys
from datetime import datetime

import requests

from scripts.aggregator.models import SourceResult, SourceType

_YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
_YOUTUBE_VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"
_TIMEOUT = 20
_SEARCH_QUERIES = [
    "claude code tutorial",
    "anthropic claude code CLI",
    "claude code agent workflow",
]
_MAX_RESULTS = 50


def _search_videos(query: str, api_key: str) -> list[str]:
    """Return list of video IDs matching the search query."""
    try:
        resp = requests.get(
            _YOUTUBE_SEARCH_URL,
            params={
                "part": "id",
                "q": query,
                "type": "video",
                "maxResults": _MAX_RESULTS,
                "order": "viewCount",
                "key": api_key,
            },
            timeout=_TIMEOUT,
        )
        if resp.status_code == 403:
            data = resp.json()
            reason = data.get("error", {}).get("errors", [{}])[0].get("reason", "unknown")
            print(f"  ✗ YouTube: API quota exceeded or key invalid (reason: {reason})", file=sys.stderr)
            return []
        resp.raise_for_status()
        items = resp.json().get("items", [])
        return [item["id"]["videoId"] for item in items if "videoId" in item.get("id", {})]
    except requests.RequestException as e:
        print(f"  ✗ YouTube search error (q='{query}'): {e}", file=sys.stderr)
        return []


def _fetch_video_details(video_ids: list[str], api_key: str) -> list[dict[str, object]]:
    """Fetch statistics and snippet for a batch of video IDs (max 50 per call)."""
    if not video_ids:
        return []
    try:
        resp = requests.get(
            _YOUTUBE_VIDEOS_URL,
            params={
                "part": "snippet,statistics",
                "id": ",".join(video_ids[:50]),
                "key": api_key,
            },
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        details = []
        for item in resp.json().get("items", []):
            snippet = item.get("snippet", {})
            stats = item.get("statistics", {})
            details.append({
                "video_id": item.get("id", ""),
                "title": snippet.get("title", ""),
                "channel_title": snippet.get("channelTitle", ""),
                "published_at": snippet.get("publishedAt", ""),
                "view_count": int(stats.get("viewCount", 0)),
                "like_count": int(stats.get("likeCount", 0)),
                "comment_count": int(stats.get("commentCount", 0)),
                "video_url": f"https://www.youtube.com/watch?v={item.get('id', '')}",
            })
        return details
    except requests.RequestException as e:
        print(f"  ✗ YouTube video detail error: {e}", file=sys.stderr)
        return []


def fetch() -> SourceResult:
    """Fetch YouTube videos covering Claude Code.

    Requires YOUTUBE_API_KEY env var. Free tier at 10,000 units/day.
    Returns empty result gracefully if key is missing.
    """
    fetched_at = datetime.utcnow()
    api_key = os.getenv("YOUTUBE_API_KEY")

    if not api_key:
        print(
            "  ! YouTube: YOUTUBE_API_KEY not set — skipping. "
            "Get a free key at console.cloud.google.com (10,000 units/day free).",
            file=sys.stderr,
        )
        return SourceResult(
            source=SourceType.YOUTUBE,
            fetched_at=fetched_at,
            records=[],
            errors=["YOUTUBE_API_KEY not configured"],
        )

    seen_ids: set[str] = set()
    all_video_ids: list[str] = []

    for query in _SEARCH_QUERIES:
        for vid_id in _search_videos(query, api_key):
            if vid_id not in seen_ids:
                seen_ids.add(vid_id)
                all_video_ids.append(vid_id)

    records = _fetch_video_details(all_video_ids, api_key)

    # Attach search context (match by position is not precise; label as multi-query)
    for rec in records:
        rec["search_queries"] = ", ".join(_SEARCH_QUERIES)

    print(f"  ✓ YouTube: {len(records)} videos fetched")
    return SourceResult(source=SourceType.YOUTUBE, fetched_at=fetched_at, records=records)
