"""Twitter/X source — mentions and engagement for Claude Code.

Requires a Twitter Developer account with at least Basic tier access ($100/mo).
Set the TWITTER_BEARER_TOKEN environment variable.

API docs: https://developer.twitter.com/en/docs/twitter-api/tweets/search/api-reference/get-tweets-search-recent
"""

from __future__ import annotations

import os
import sys
from datetime import datetime

import requests

from scripts.aggregator.models import SourceResult, SourceType

_TWITTER_SEARCH_URL = "https://api.twitter.com/2/tweets/search/recent"
_TIMEOUT = 20
_SEARCH_QUERIES = [
    "(claude code) -is:retweet lang:en",
    "(claude-code anthropic) -is:retweet lang:en",
    '("Claude Code" CLI) -is:retweet lang:en',
]
_TWEET_FIELDS = "created_at,author_id,public_metrics,lang,entities"
_MAX_RESULTS = 100


def _search_tweets(
    query: str,
    bearer_token: str,
    next_token: str | None = None,
) -> tuple[list[dict[str, object]], str | None]:
    headers = {"Authorization": f"Bearer {bearer_token}"}
    params: dict[str, object] = {
        "query": query,
        "max_results": _MAX_RESULTS,
        "tweet.fields": _TWEET_FIELDS,
    }
    if next_token:
        params["next_token"] = next_token

    try:
        resp = requests.get(_TWITTER_SEARCH_URL, headers=headers, params=params, timeout=_TIMEOUT)
        if resp.status_code == 401:
            print("  ✗ Twitter: invalid bearer token (check TWITTER_BEARER_TOKEN)", file=sys.stderr)
            return [], None
        if resp.status_code == 403:
            print(
                "  ✗ Twitter: access forbidden — Basic tier or higher required ($100/mo)",
                file=sys.stderr,
            )
            return [], None
        if resp.status_code == 429:
            print("  ✗ Twitter: rate limit reached", file=sys.stderr)
            return [], None
        resp.raise_for_status()
        body = resp.json()
        tweets: list[dict[str, object]] = body.get("data", [])
        meta = body.get("meta", {})
        return tweets, meta.get("next_token")
    except requests.RequestException as e:
        print(f"  ✗ Twitter search error (q='{query}'): {e}", file=sys.stderr)
        return [], None


def fetch() -> SourceResult:
    """Fetch recent tweets mentioning Claude Code.

    Requires TWITTER_BEARER_TOKEN env var (Twitter Developer Basic tier or higher).
    Returns empty result gracefully if token is missing.
    """
    fetched_at = datetime.utcnow()
    bearer_token = os.getenv("TWITTER_BEARER_TOKEN")

    if not bearer_token:
        print(
            "  ! Twitter: TWITTER_BEARER_TOKEN not set — skipping. "
            "Sign up at developer.twitter.com (Basic tier ~$100/mo).",
            file=sys.stderr,
        )
        return SourceResult(
            source=SourceType.TWITTER,
            fetched_at=fetched_at,
            records=[],
            errors=["TWITTER_BEARER_TOKEN not configured"],
        )

    seen_ids: set[str] = set()
    records: list[dict[str, object]] = []

    for query in _SEARCH_QUERIES:
        tweets, _next = _search_tweets(query, bearer_token)
        for tweet in tweets:
            tid = str(tweet.get("id", ""))
            if tid in seen_ids:
                continue
            seen_ids.add(tid)
            metrics: dict[str, object] = tweet.get("public_metrics", {})  # type: ignore[assignment]
            records.append({
                "id": tid,
                "text": tweet.get("text", ""),
                "author_id": tweet.get("author_id", ""),
                "created_at": tweet.get("created_at", ""),
                "retweet_count": metrics.get("retweet_count", 0),
                "reply_count": metrics.get("reply_count", 0),
                "like_count": metrics.get("like_count", 0),
                "quote_count": metrics.get("quote_count", 0),
                "tweet_url": f"https://twitter.com/i/web/status/{tid}",
                "search_query": query,
            })

    print(f"  ✓ Twitter/X: {len(records)} tweets fetched")
    return SourceResult(source=SourceType.TWITTER, fetched_at=fetched_at, records=records)
