"""Reddit source — community discussions about Claude Code.

Uses the public Reddit JSON API (no auth required for read-only search).
For higher rate limits, set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET env vars
to use OAuth2 app credentials (free, register at reddit.com/prefs/apps).
"""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime

import requests

from scripts.aggregator.models import SourceResult, SourceType

_REDDIT_SEARCH_URL = "https://www.reddit.com/search.json"
_REDDIT_OAUTH_TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
_REDDIT_OAUTH_SEARCH_URL = "https://oauth.reddit.com/search"
_USER_AGENT = "awesome-claude-code bot/1.0"
_TIMEOUT = 20
_SUBREDDITS = ["ClaudeAI", "LocalLLaMA", "AIAssistants", "ChatGPT", "MachineLearning"]
_SEARCH_QUERIES = ["claude code", "claude-code CLI", "anthropic claude code"]


def _get_oauth_token(client_id: str, client_secret: str) -> str | None:
    try:
        resp = requests.post(
            _REDDIT_OAUTH_TOKEN_URL,
            auth=(client_id, client_secret),
            data={"grant_type": "client_credentials"},
            headers={"User-Agent": _USER_AGENT},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json().get("access_token")
    except requests.RequestException as e:
        print(f"  ✗ Reddit OAuth error: {e}", file=sys.stderr)
        return None


def _search_public(query: str, subreddit: str | None = None) -> list[dict[str, object]]:
    """Search Reddit via the public (unauthenticated) JSON API."""
    params: dict[str, object] = {
        "q": query,
        "sort": "relevance",
        "t": "month",
        "limit": 25,
        "type": "link",
    }
    if subreddit:
        params["restrict_sr"] = "on"
        url = f"https://www.reddit.com/r/{subreddit}/search.json"
    else:
        url = _REDDIT_SEARCH_URL

    try:
        resp = requests.get(
            url,
            params=params,
            headers={"User-Agent": _USER_AGENT},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        children = resp.json().get("data", {}).get("children", [])
        return [c["data"] for c in children]
    except requests.RequestException as e:
        print(f"  ✗ Reddit public search error (q='{query}'): {e}", file=sys.stderr)
        return []


def _search_oauth(query: str, token: str) -> list[dict[str, object]]:
    try:
        resp = requests.get(
            _REDDIT_OAUTH_SEARCH_URL,
            params={"q": query, "sort": "relevance", "t": "month", "limit": 50, "type": "link"},
            headers={"Authorization": f"Bearer {token}", "User-Agent": _USER_AGENT},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        children = resp.json().get("data", {}).get("children", [])
        return [c["data"] for c in children]
    except requests.RequestException as e:
        print(f"  ✗ Reddit OAuth search error (q='{query}'): {e}", file=sys.stderr)
        return []


def fetch() -> SourceResult:
    """Fetch Reddit posts mentioning Claude Code."""
    fetched_at = datetime.utcnow()

    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    token: str | None = None

    if client_id and client_secret:
        token = _get_oauth_token(client_id, client_secret)
        if token:
            print("  ✓ Reddit: using OAuth2 (higher rate limits)")
        else:
            print("  ! Reddit: OAuth failed, falling back to public API")
    else:
        print("  ! Reddit: no credentials found, using public API (lower rate limits)")

    seen_ids: set[str] = set()
    records: list[dict[str, object]] = []

    for query in _SEARCH_QUERIES:
        posts: list[dict[str, object]] = []
        if token:
            posts = _search_oauth(query, token)
        else:
            for subreddit in _SUBREDDITS:
                posts.extend(_search_public(query, subreddit))
                time.sleep(0.5)  # be polite to the public API

        for post in posts:
            pid = post.get("id", "")
            if pid in seen_ids:
                continue
            seen_ids.add(str(pid))
            records.append({
                "id": pid,
                "title": post.get("title", ""),
                "url": post.get("url", ""),
                "reddit_url": f"https://reddit.com{post.get('permalink', '')}",
                "subreddit": post.get("subreddit", ""),
                "score": post.get("score", 0),
                "num_comments": post.get("num_comments", 0),
                "author": post.get("author", ""),
                "created_utc": post.get("created_utc", 0),
                "search_query": query,
            })

    print(f"  ✓ Reddit: {len(records)} posts fetched")
    return SourceResult(source=SourceType.REDDIT, fetched_at=fetched_at, records=records)
