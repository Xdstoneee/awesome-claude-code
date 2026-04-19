#!/usr/bin/env python3
"""
Multi-source data aggregator — "God's Eye" view of the Claude Code ecosystem.

Fetches data from GitHub, npm, PyPI, HackerNews, Reddit, VS Code Marketplace,
Twitter/X (paid), and YouTube (free key), then writes per-source CSVs and a
unified ecosystem-pulse.csv under data/aggregated/.

Environment variables (set what you have; unset sources are skipped gracefully):
  GITHUB_TOKEN        — Avoids GitHub API rate limits (free)
  REDDIT_CLIENT_ID    — Reddit OAuth app client ID (free, register at reddit.com/prefs/apps)
  REDDIT_CLIENT_SECRET— Reddit OAuth app secret (free)
  TWITTER_BEARER_TOKEN— Twitter API v2 bearer token (Basic tier ~$100/mo)
  YOUTUBE_API_KEY     — Google Cloud YouTube Data API v3 key (free, 10k units/day)
"""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path

from scripts.aggregator.models import SourceResult, SourceType
from scripts.aggregator.sources import hackernews, npm, pypi, reddit, vscode, youtube
from scripts.aggregator.sources import twitter as twitter_src
from scripts.utils.repo_root import find_repo_root

REPO_ROOT = find_repo_root(Path(__file__))
DATA_DIR = REPO_ROOT / "data" / "aggregated"

_SOURCE_FIELDNAMES: dict[SourceType, list[str]] = {
    SourceType.NPM: ["package", "downloads_last_month", "start", "end"],
    SourceType.PYPI: [
        "package", "version", "summary", "home_page",
        "downloads_last_day", "downloads_last_week", "downloads_last_month",
    ],
    SourceType.HACKERNEWS: [
        "id", "title", "url", "hn_url", "points", "num_comments", "author", "created_at", "search_query",
    ],
    SourceType.REDDIT: [
        "id", "title", "url", "reddit_url", "subreddit", "score", "num_comments",
        "author", "created_utc", "search_query",
    ],
    SourceType.VSCODE: [
        "extension_id", "name", "display_name", "publisher", "short_description",
        "install_count", "rating", "rating_count", "last_updated", "marketplace_url", "search_term",
    ],
    SourceType.TWITTER: [
        "id", "text", "author_id", "created_at", "retweet_count", "reply_count",
        "like_count", "quote_count", "tweet_url", "search_query",
    ],
    SourceType.YOUTUBE: [
        "video_id", "title", "channel_title", "published_at",
        "view_count", "like_count", "comment_count", "video_url", "search_queries",
    ],
}

_SOURCE_FILENAMES: dict[SourceType, str] = {
    SourceType.NPM: "npm-pulse.csv",
    SourceType.PYPI: "pypi-pulse.csv",
    SourceType.HACKERNEWS: "hackernews-pulse.csv",
    SourceType.REDDIT: "reddit-pulse.csv",
    SourceType.VSCODE: "vscode-pulse.csv",
    SourceType.TWITTER: "twitter-pulse.csv",
    SourceType.YOUTUBE: "youtube-pulse.csv",
}


def _write_source_csv(result: SourceResult, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = _SOURCE_FILENAMES[result.source]
    path = output_dir / filename
    fieldnames = _SOURCE_FIELDNAMES.get(result.source, [])
    if not fieldnames and result.records:
        fieldnames = list(result.records[0].keys())

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(result.records)

    return path


def _write_ecosystem_pulse(results: list[SourceResult], output_dir: Path) -> Path:
    """Write a unified summary CSV with one row per source."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "ecosystem-pulse.csv"
    fieldnames = [
        "source", "fetched_at", "record_count", "errors", "status",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow({
                "source": r.source.value,
                "fetched_at": r.fetched_at.isoformat(),
                "record_count": r.record_count,
                "errors": "; ".join(r.errors) if r.errors else "",
                "status": "ok" if r.success else "error",
            })
    return path


def _run_source(name: str, fn: object) -> SourceResult | None:
    print(f"\n[{name}]")
    try:
        return fn()  # type: ignore[operator]
    except Exception as e:
        print(f"  ✗ Unexpected error in {name}: {e}", file=sys.stderr)
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Aggregate multi-source Claude Code ecosystem data")
    parser.add_argument(
        "--sources",
        nargs="+",
        choices=[s.value for s in SourceType if s != SourceType.GITHUB],
        default=None,
        help="Limit which sources to fetch (default: all)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DATA_DIR,
        help="Output directory for CSVs (default: data/aggregated/)",
    )
    args = parser.parse_args(argv)

    enabled = set(args.sources) if args.sources else {s.value for s in SourceType if s != SourceType.GITHUB}
    output_dir: Path = args.output_dir

    source_map: dict[str, object] = {
        SourceType.NPM.value: npm.fetch,
        SourceType.PYPI.value: pypi.fetch,
        SourceType.HACKERNEWS.value: hackernews.fetch,
        SourceType.REDDIT.value: reddit.fetch,
        SourceType.VSCODE.value: vscode.fetch,
        SourceType.TWITTER.value: twitter_src.fetch,
        SourceType.YOUTUBE.value: youtube.fetch,
    }

    print(f"=== Claude Code Ecosystem Pulse — {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')} ===")
    print(f"Sources enabled: {', '.join(sorted(enabled))}")

    results: list[SourceResult] = []
    for source_name in sorted(enabled):
        fn = source_map.get(source_name)
        if not fn:
            continue
        result = _run_source(source_name.upper(), fn)
        if result:
            results.append(result)
            csv_path = _write_source_csv(result, output_dir)
            print(f"  → {csv_path.relative_to(REPO_ROOT)}")

    if results:
        pulse_path = _write_ecosystem_pulse(results, output_dir)
        print(f"\n=== Summary written to {pulse_path.relative_to(REPO_ROOT)} ===")
        for r in results:
            status = "✓" if r.success else "✗"
            print(f"  {status} {r.source.value:<15} {r.record_count:>5} records")

    return 0


if __name__ == "__main__":
    sys.exit(main())
