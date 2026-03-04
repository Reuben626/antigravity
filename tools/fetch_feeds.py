"""
fetch_feeds.py — RSS Feed Fetcher for AI Pulse Dashboard
=========================================================
Fetches articles from AI newsletter RSS feeds, transforms them into
clean JSON matching the Output Schema, and writes to dashboard/public/feeds.json.

Usage:
    python tools/fetch_feeds.py
"""

import hashlib
import json
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path

# ─── Configuration ───────────────────────────────────────────────────────────

FEEDS = [
    {
        "url": "https://bensbites.substack.com/feed",
        "source": "bens_bites",
        "sourceName": "Ben's Bites",
    },
    {
        "url": "https://rss.beehiiv.com/feeds/2R3C6Bt5wj.xml",
        "source": "the_rundown_ai",
        "sourceName": "The Rundown AI",
    },
]

# Output path relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = PROJECT_ROOT / "dashboard" / "public" / "feeds.json"

# Time window: only articles from the last 24 hours
HOURS_WINDOW = 24


# ─── Helpers ─────────────────────────────────────────────────────────────────

def strip_html(html_string: str) -> str:
    """Remove all HTML tags and decode entities to plain text."""
    if not html_string:
        return ""
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", html_string)
    # Decode HTML entities
    text = unescape(text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def generate_id(link: str, pub_date: str) -> str:
    """Generate a deterministic ID from link + pubDate."""
    raw = f"{link}{pub_date}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def parse_date(date_str: str) -> datetime | None:
    """Parse RFC 2822 or ISO 8601 date strings to timezone-aware datetime."""
    if not date_str:
        return None
    try:
        return parsedate_to_datetime(date_str)
    except Exception:
        pass
    # Fallback: try ISO 8601
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        pass
    return None


def fetch_feed(url: str, timeout: int = 15) -> str | None:
    """Fetch raw XML string from a feed URL."""
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "AIPulseDashboard/1.0 (RSS Reader)",
                "Accept": "application/rss+xml, application/xml, text/xml",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.read().decode("utf-8")
    except Exception as e:
        print(f"  ⚠️  Failed to fetch {url}: {e}", file=sys.stderr)
        return None


def parse_feed(xml_str: str, feed_config: dict, cutoff: datetime) -> list[dict]:
    """Parse RSS XML and return list of article dicts matching Output Schema."""
    articles = []
    try:
        root = ET.fromstring(xml_str)
    except ET.ParseError as e:
        print(f"  ⚠️  XML parse error for {feed_config['source']}: {e}", file=sys.stderr)
        return articles

    now_utc = datetime.now(timezone.utc).isoformat()

    # Find all <item> elements (works for both RSS 2.0 structures)
    items = root.findall(".//item")

    for item in items:
        title = item.findtext("title", "").strip()
        link = item.findtext("link", "").strip()
        pub_date_raw = item.findtext("pubDate", "").strip()
        description = item.findtext("description", "")
        author = item.findtext("author") or item.findtext("{http://purl.org/dc/elements/1.1/}creator")

        # Parse categories
        categories = [cat.text for cat in item.findall("category") if cat.text]

        # Parse and filter by date
        published_dt = parse_date(pub_date_raw)
        if published_dt is None:
            continue
        if published_dt < cutoff:
            continue

        # Build article object
        article = {
            "id": generate_id(link, pub_date_raw),
            "title": title,
            "summary": strip_html(description)[:500],  # Cap at 500 chars
            "url": link,
            "source": feed_config["source"],
            "sourceName": feed_config["sourceName"],
            "author": author.strip() if author else None,
            "publishedAt": published_dt.isoformat(),
            "fetchedAt": now_utc,
            "categories": categories,
            "isSaved": False,
        }
        articles.append(article)

    return articles


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    print("🚀 AI Pulse Dashboard — Feed Fetcher")
    print("=" * 45)

    cutoff = datetime.now(timezone.utc) - timedelta(hours=HOURS_WINDOW)
    print(f"📅 Cutoff: {cutoff.isoformat()} ({HOURS_WINDOW}h window)")

    all_articles = []
    seen_ids = set()

    for feed in FEEDS:
        print(f"\n📡 Fetching: {feed['sourceName']} ({feed['source']})")
        xml_str = fetch_feed(feed["url"])
        if xml_str is None:
            continue

        articles = parse_feed(xml_str, feed, cutoff)
        print(f"   ✅ Found {len(articles)} article(s) within 24h window")

        # Deduplicate
        for article in articles:
            if article["id"] not in seen_ids:
                seen_ids.add(article["id"])
                all_articles.append(article)

    # Sort by publishedAt descending (newest first)
    all_articles.sort(key=lambda a: a["publishedAt"], reverse=True)

    # Ensure output directory exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_articles, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Done! Wrote {len(all_articles)} articles to {OUTPUT_PATH}")
    return all_articles


if __name__ == "__main__":
    main()
