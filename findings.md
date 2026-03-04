# 🔍 findings.md — Research & Discoveries

> Populated as research is completed and constraints are discovered.

---

## 📅 Log

| Date | Finding | Impact |
|------|---------|--------|
| 2026-03-03 | Project initialized | Protocol 0 complete |
| 2026-03-03 | Ben's Bites uses Substack RSS | Feed URL: `https://bensbites.substack.com/feed` — standard XML RSS 2.0 |
| 2026-03-03 | The Rundown AI uses beehiiv RSS | Feed URL: `https://rss.beehiiv.com/feeds/2R3C6Bt5wj.xml` |
| 2026-03-03 | RSS is the cleanest approach | Both platforms expose public RSS — no scraping or API keys required |
| 2026-03-03 | RSS items contain HTML in `description` | Must strip HTML to produce clean plain-text summaries |
| 2026-03-03 | Feed items have `title`, `link`, `pubDate`, `description`, `author`, `category` | Maps directly to our Input Schema |

---

## 🌐 External Resources

- **Substack RSS format**: `https://<publication>.substack.com/feed` — standard RSS 2.0 XML
- **beehiiv RSS format**: `https://rss.beehiiv.com/feeds/<id>.xml` — standard RSS 2.0 XML
- **CORS Note**: RSS feeds are XML on different domains — the frontend cannot fetch these directly due to CORS. Options: (a) use a CORS proxy, (b) use a Python backend to fetch + serve as JSON, or (c) use a public CORS proxy like `allorigins` or `corsproxy.io`.

---

## ⚠️ Constraints & Gotchas

1. **CORS** — Browsers block cross-origin XML requests. The frontend needs a proxy to fetch RSS feeds.
2. **HTML in descriptions** — RSS `<description>` fields contain raw HTML that must be sanitized/stripped.
3. **pubDate formats** — Substack and beehiiv may use slightly different date formats; must normalize to ISO 8601.
4. **Rate awareness** — Feed providers may rate-limit aggressive polling. 24hr refresh window is safe.

---

## 🔗 Relevant GitHub Repos / References

- `scrape-substack` Python library (GitHub) — unofficial Substack API wrapper
- `Carsoncantcode/newsletter-scraper` — beehiiv publication scraper
- Apify Newsletter Archive Scraper — supports Substack, beehiiv, Ghost
