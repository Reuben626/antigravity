"""
fetch_feeds.py — POD Research Feed Fetcher
============================================
Fetches content from Print on Demand research sources:
- Printful blog (RSS)       — embroidery & POD tips
- Printify blog (RSS)       — POD business content
- eRank blog (RSS)          — Etsy SEO & POD trends
- ProfitTree blog (scrape)  — Etsy seller strategies & POD profit research
- Amazon Novelty Shirts     — bestselling graphic/novelty tee rankings
- Amazon Merch (scrape)     — Merch by Amazon shirt category bestsellers

Usage:
    python tools/fetch_feeds.py
"""

import hashlib
import json
import re
import sys
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path

# ─── Configuration ───────────────────────────────────────────────────────────

RSS_FEEDS = [
    {
        "url": "https://www.printful.com/blog/feed",
        "source": "printful",
        "sourceName": "Printful",
    },
    {
        "url": "https://printify.com/blog/category/print-on-demand/feed/",
        "source": "printify",
        "sourceName": "Printify",
    },
    {
        "url": "https://help.erank.com/feed/",
        "source": "erank",
        "sourceName": "eRank",
    },
]

# Amazon bestseller pages for graphic/novelty/Merch shirts
AMAZON_PAGES = [
    {
        "url": "https://www.amazon.com/gp/bestsellers/fashion/9056985011",  # Novelty & More Graphic Tees
        "label": "Novelty Graphic Tees",
        "source": "amazon",
        "sourceName": "Amazon",
    },
    {
        "url": "https://www.amazon.com/gp/bestsellers/fashion/7147441011",  # Men's Fashion top-level
        "label": "Men's Fashion",
        "source": "amazon",
        "sourceName": "Amazon",
    },
]

PROFITTREE_URL = "https://profittree.io/blog"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = PROJECT_ROOT / "dashboard" / "public" / "feeds.json"
# 30-day window: POD blogs publish weekly/bi-weekly
HOURS_WINDOW = 720


# ─── Helpers ─────────────────────────────────────────────────────────────────

def strip_html(html_string):
    if not html_string:
        return ""
    text = re.sub(r"<[^>]+>", " ", html_string)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def generate_id(link, extra=""):
    raw = f"{link}{extra}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def parse_date(date_str):
    if not date_str:
        return None
    try:
        return parsedate_to_datetime(date_str)
    except Exception:
        pass
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        pass
    return None


def fetch_url(url, timeout=15, extra_headers=None):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    if extra_headers:
        headers.update(extra_headers)
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  ⚠️  Failed to fetch {url}: {e}", file=sys.stderr)
        return None


# ─── RSS Feed Parser ─────────────────────────────────────────────────────────

def parse_rss_feed(xml_str, feed_config, cutoff):
    articles = []
    try:
        root = ET.fromstring(xml_str)
    except ET.ParseError as e:
        print(f"  ⚠️  XML parse error for {feed_config['source']}: {e}", file=sys.stderr)
        return articles

    now_utc = datetime.now(timezone.utc).isoformat()
    items = root.findall(".//item")

    for item in items:
        title = item.findtext("title", "").strip()
        link = item.findtext("link", "").strip()
        pub_date_raw = item.findtext("pubDate", "").strip()
        description = item.findtext("description", "") or item.findtext("{http://purl.org/rss/1.0/modules/content/}encoded", "")
        author = item.findtext("author") or item.findtext("{http://purl.org/dc/elements/1.1/}creator")
        categories = [cat.text for cat in item.findall("category") if cat.text]

        published_dt = parse_date(pub_date_raw)
        if published_dt is None:
            continue
        if published_dt < cutoff:
            continue

        articles.append({
            "id": generate_id(link, pub_date_raw),
            "title": title,
            "summary": strip_html(description)[:500],
            "url": link,
            "source": feed_config["source"],
            "sourceName": feed_config["sourceName"],
            "author": author.strip() if author else None,
            "publishedAt": published_dt.isoformat(),
            "fetchedAt": now_utc,
            "categories": categories,
            "isSaved": False,
        })

    return articles


# ─── Amazon Bestseller Scraper ───────────────────────────────────────────────

def scrape_amazon_bestsellers(page_config, max_items=20):
    """Scrape Amazon bestseller page for shirt/graphic tee rankings."""
    url = page_config["url"]
    print(f"   🔍 Category: '{page_config['label']}'")

    html = fetch_url(url)
    if not html:
        return []

    now_utc = datetime.now(timezone.utc).isoformat()
    articles = []
    seen_urls = set()

    # Amazon bestsellers embed product data — extract rank, title, ASIN, and URL
    # Pattern: rank number + product title + product link
    product_pattern = re.compile(
        r'<span class="[^"]*zg-bdg-text[^"]*"[^>]*>#?(\d+)</span>.*?'
        r'<div class="[^"]*p13n-sc-uncoverable-faceout[^"]*".*?'
        r'<a[^>]+href="(/[^"]+/dp/[A-Z0-9]{10}[^"]*)"[^>]*>.*?'
        r'<span[^>]*>([^<]{5,200})</span>',
        re.DOTALL
    )

    # Simpler fallback: extract all product links with ASINs and titles from the page
    asin_pattern = re.compile(r'/dp/([A-Z0-9]{10})/')
    title_pattern = re.compile(
        r'class="[^"]*s-color-base[^"]*"[^>]*>([^<]{10,200})</span>'
    )

    # Try JSON-LD structured data first
    jsonld_pattern = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.DOTALL)
    for jsonld_str in jsonld_pattern.findall(html):
        try:
            data = json.loads(jsonld_str)
            if isinstance(data, list):
                items = data
            else:
                items = [data]
            for item in items:
                if item.get("@type") != "Product":
                    continue
                name = item.get("name", "").strip()
                item_url = item.get("url", "").strip()
                if not name or not item_url or item_url in seen_urls:
                    continue
                seen_urls.add(item_url)

                offers = item.get("offers", {})
                price = ""
                if isinstance(offers, dict):
                    price = offers.get("price", "")
                    currency = offers.get("priceCurrency", "USD")
                    if price:
                        price = f"{currency} {price}"

                rating = item.get("aggregateRating", {})
                rating_str = ""
                if isinstance(rating, dict):
                    rv = rating.get("ratingValue", "")
                    rc = rating.get("reviewCount", "")
                    if rv:
                        rating_str = f"⭐ {rv}/5"
                        if rc:
                            rating_str += f" ({rc} reviews)"

                summary_parts = [p_config for p_config in [
                    f"#{len(articles)+1} bestseller in {page_config['label']}",
                    price,
                    rating_str,
                ] if p_config]

                articles.append({
                    "id": generate_id(item_url),
                    "title": name,
                    "summary": " · ".join(summary_parts),
                    "url": item_url if item_url.startswith("http") else f"https://www.amazon.com{item_url}",
                    "source": page_config["source"],
                    "sourceName": page_config["sourceName"],
                    "author": None,
                    "publishedAt": now_utc,
                    "fetchedAt": now_utc,
                    "categories": [page_config["label"], "Bestseller", "Print on Demand"],
                    "isSaved": False,
                })
                if len(articles) >= max_items:
                    break
        except (json.JSONDecodeError, KeyError):
            continue
        if len(articles) >= max_items:
            break

    # Fallback: extract product links + titles via regex from HTML
    if not articles:
        links = re.findall(r'href="(https://www\.amazon\.com/[^"]+/dp/[A-Z0-9]{10}[^"]*)"', html)
        titles = re.findall(r'class="[^"]*a-size-[^"]*"[^>]*>([^<]{15,150})</span>', html)
        for i, (link, title) in enumerate(zip(links, titles)):
            if link in seen_urls:
                continue
            seen_urls.add(link)
            clean_link = link.split("?")[0]  # remove query params
            articles.append({
                "id": generate_id(clean_link),
                "title": unescape(title.strip()),
                "summary": f"#{i+1} bestseller in {page_config['label']} on Amazon",
                "url": clean_link,
                "source": page_config["source"],
                "sourceName": page_config["sourceName"],
                "author": None,
                "publishedAt": now_utc,
                "fetchedAt": now_utc,
                "categories": [page_config["label"], "Bestseller"],
                "isSaved": False,
            })
            if len(articles) >= max_items:
                break

    return articles


# ─── ProfitTree Blog Scraper ─────────────────────────────────────────────────

def scrape_profittree(max_items=10):
    """Scrape ProfitTree blog for Etsy/POD research articles."""
    print(f"   🔍 Scraping: {PROFITTREE_URL}")
    html = fetch_url(PROFITTREE_URL)
    if not html:
        return []

    now_utc = datetime.now(timezone.utc).isoformat()
    articles = []
    seen_urls = set()

    # ProfitTree uses typical blog card structure — extract article links and titles
    # Try Open Graph / meta tags for structured data
    jsonld_pattern = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.DOTALL)
    for jsonld_str in jsonld_pattern.findall(html):
        try:
            data = json.loads(jsonld_str)
            items = data if isinstance(data, list) else [data]
            for item in items:
                if item.get("@type") not in ("BlogPosting", "Article", "NewsArticle"):
                    continue
                title = item.get("headline", item.get("name", "")).strip()
                url = item.get("url", "").strip()
                desc = strip_html(item.get("description", ""))
                date_str = item.get("datePublished", item.get("dateModified", ""))
                if not title or not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                published_dt = parse_date(date_str)
                published = published_dt.isoformat() if published_dt else now_utc
                articles.append({
                    "id": generate_id(url),
                    "title": title,
                    "summary": desc[:500] if desc else "POD and Etsy seller research from ProfitTree.",
                    "url": url,
                    "source": "profittree",
                    "sourceName": "ProfitTree",
                    "author": None,
                    "publishedAt": published,
                    "fetchedAt": now_utc,
                    "categories": ["Etsy", "Print on Demand", "Research"],
                    "isSaved": False,
                })
                if len(articles) >= max_items:
                    break
        except (json.JSONDecodeError, KeyError):
            continue
        if len(articles) >= max_items:
            break

    # Fallback: anchor tag scraping
    if not articles:
        link_pattern = re.compile(
            r'<a[^>]+href="(https://profittree\.io/blog/[^"]+)"[^>]*>\s*([^<]{10,200})',
            re.IGNORECASE
        )
        for match in link_pattern.finditer(html):
            url, title = match.group(1).strip(), match.group(2).strip()
            if url in seen_urls or not title:
                continue
            seen_urls.add(url)
            articles.append({
                "id": generate_id(url),
                "title": unescape(title),
                "summary": "POD and Etsy seller research from ProfitTree.",
                "url": url,
                "source": "profittree",
                "sourceName": "ProfitTree",
                "author": None,
                "publishedAt": now_utc,
                "fetchedAt": now_utc,
                "categories": ["Etsy", "Print on Demand", "Research"],
                "isSaved": False,
            })
            if len(articles) >= max_items:
                break

    return articles


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    print("🔬  POD Research — Feed Fetcher")
    print("=" * 45)

    cutoff = datetime.now(timezone.utc) - timedelta(hours=HOURS_WINDOW)
    print(f"📅 Blog cutoff: last {HOURS_WINDOW}h | Bestsellers always fresh")

    all_articles = []
    seen_ids = set()

    # ── RSS Feeds (blogs) ──
    for feed in RSS_FEEDS:
        print(f"\n📡 RSS: {feed['sourceName']}")
        xml_str = fetch_url(feed["url"], extra_headers={
            "Accept": "application/rss+xml, application/xml, text/xml"
        })
        if xml_str is None:
            continue
        articles = parse_rss_feed(xml_str, feed, cutoff)
        print(f"   ✅ {len(articles)} article(s)")
        for a in articles:
            if a["id"] not in seen_ids:
                seen_ids.add(a["id"])
                all_articles.append(a)

    # ── ProfitTree blog ──
    print(f"\n🌳 Scraping: ProfitTree")
    pt_articles = scrape_profittree()
    print(f"   ✅ {len(pt_articles)} article(s)")
    for a in pt_articles:
        if a["id"] not in seen_ids:
            seen_ids.add(a["id"])
            all_articles.append(a)

    # ── Amazon Bestsellers ──
    print(f"\n🛒 Scraping: Amazon Bestsellers")
    for page in AMAZON_PAGES:
        listings = scrape_amazon_bestsellers(page)
        print(f"   ✅ '{page['label']}': {len(listings)} item(s)")
        for a in listings:
            if a["id"] not in seen_ids:
                seen_ids.add(a["id"])
                all_articles.append(a)

    # Sort: blog posts by date desc first, then Amazon listings
    blog = [a for a in all_articles if a["source"] != "amazon"]
    amazon = [a for a in all_articles if a["source"] == "amazon"]
    blog.sort(key=lambda a: a["publishedAt"], reverse=True)
    all_articles = blog + amazon

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_articles, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Done! Wrote {len(all_articles)} items to {OUTPUT_PATH}")
    print(f"   📰 Blog: {len(blog)} | 🛒 Amazon: {len(amazon)}")


if __name__ == "__main__":
    main()
