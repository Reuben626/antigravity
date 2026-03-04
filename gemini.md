# 📜 gemini.md — Project Constitution

> **This file is LAW.** Only update when schemas change, rules are added, or architecture is modified.

---

## 🗂️ Project Identity

- **Project Name:** AI Pulse Dashboard
- **North Star:** A beautiful, interactive dashboard that aggregates the latest AI news from top newsletters, refreshes every 24 hours, and lets the user save/bookmark articles — all persisting across page refreshes.
- **System Pilot Version:** B.L.A.S.T. v1.0
- **Initialized:** 2026-03-03

---

## 🧬 Data Schema

### Input Shape (Raw RSS Item)
```json
{
  "title": "string — article headline",
  "link": "string — URL to original article",
  "pubDate": "string — ISO 8601 publication date",
  "description": "string — article summary / snippet (HTML)",
  "source": "string — 'bens_bites' | 'the_rundown_ai'",
  "author": "string — author name (optional)",
  "categories": ["string — tags/categories (optional)"]
}
```

### Output Shape (Processed Article — Payload)
```json
{
  "id": "string — deterministic hash of link+pubDate",
  "title": "string — cleaned headline",
  "summary": "string — plain-text summary (stripped HTML)",
  "url": "string — original article URL",
  "source": "string — 'bens_bites' | 'the_rundown_ai'",
  "sourceName": "string — 'Ben's Bites' | 'The Rundown AI'",
  "author": "string | null",
  "publishedAt": "string — ISO 8601 UTC",
  "fetchedAt": "string — ISO 8601 UTC",
  "categories": ["string"],
  "isSaved": "boolean — user bookmark state (client-side)"
}
```

### Saved Articles Store (localStorage)
```json
{
  "savedArticles": ["string — article id"],
  "lastFetchTimestamp": "string — ISO 8601 UTC"
}
```

---

## 🏗️ Architectural Invariants

1. **Tools are atomic** — each script in `tools/` does exactly one thing.
2. **`.tmp/` is ephemeral** — never rely on temp files surviving between runs.
3. **`.env` is the only secrets store** — no hardcoded credentials ever.
4. **SOP before code** — if logic changes, update `architecture/` first.
5. **No guessing** — if business logic is ambiguous, halt and ask.

---

## 📏 Behavioral Rules

1. **RSS-first** — Use RSS feeds as the primary data source; no aggressive scraping.
2. **24-hour window** — Only display articles published within the last 24 hours.
3. **No duplicates** — Deduplicate articles by their deterministic `id` hash.
4. **Saved articles persist** — Bookmarks survive page refreshes via localStorage (Supabase later).
5. **Graceful degradation** — If a feed is unreachable, show cached data + error badge.
6. **Gorgeous UI** — Premium glassmorphism, dark mode, smooth micro-animations. No boring defaults.

---

## 🔗 Integrations & Credentials

| Service | Status | Feed URL |
|---------|--------|----------|
| Ben's Bites (Substack) | ✅ Verified | `https://bensbites.substack.com/feed` |
| The Rundown AI (beehiiv) | ✅ Verified | `https://rss.beehiiv.com/feeds/2R3C6Bt5wj.xml` |
| Supabase | ⏳ Future Phase | `.env` |

---

## 🏛️ Architecture Overview

```
├── gemini.md              ← Project Constitution
├── .env                   ← API Keys/Secrets (future)
├── architecture/          ← Layer 1: SOPs (Markdown)
│   └── scraper-sop.md     ← How the RSS scraper works
├── tools/                 ← Layer 3: Python scripts
│   └── fetch_feeds.py     ← RSS feed fetcher
├── dashboard/             ← Frontend (Vite app)
│   ├── index.html
│   ├── index.css
│   └── main.js
└── .tmp/                  ← Temporary workbench
```

---

## 📋 Maintenance Log

| Date | Change | Reason |
|------|--------|--------|
| 2026-03-03 | Initial constitution created | Protocol 0 Initialization |
| 2026-03-03 | Schema locked, sources verified | Blueprint phase complete |
