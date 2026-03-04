# RSS Scraper — Standard Operating Procedure

## Goal
Fetch the latest articles from AI newsletter RSS feeds, transform them into a clean JSON payload, and write to `dashboard/public/feeds.json` for the frontend to consume.

## Sources

| Newsletter | Platform | Feed URL |
|-----------|----------|----------|
| Ben's Bites | Substack | `https://bensbites.substack.com/feed` |
| The Rundown AI | beehiiv | `https://rss.beehiiv.com/feeds/2R3C6Bt5wj.xml` |

## Pipeline

1. **Fetch** — HTTP GET each RSS feed URL (timeout: 15s)
2. **Parse** — Parse XML using `xml.etree.ElementTree`
3. **Transform** — For each `<item>`:
   - Extract `title`, `link`, `pubDate`, `description`, `author`, `category`
   - Strip HTML from `description` → plain text `summary`
   - Normalize `pubDate` → ISO 8601 UTC `publishedAt`
   - Generate deterministic `id` = SHA-256 hash of `link + pubDate`
   - Tag with `source` identifier and `sourceName`
4. **Filter** — Only keep articles where `publishedAt` is within the last 24 hours
5. **Deduplicate** — Remove any duplicate `id` values
6. **Output** — Write JSON array to `dashboard/public/feeds.json`

## Error Handling

- If a feed is unreachable → log warning, skip that feed, continue with others
- If XML parsing fails → log error with feed URL, skip
- If zero articles after filtering → write empty array `[]`

## Edge Cases

- `pubDate` format varies between Substack (RFC 2822) and beehiiv → use `email.utils.parsedate_to_datetime`
- `description` may contain full HTML with images/links → strip all tags
- Some items may lack `author` or `category` → default to `null` / `[]`
