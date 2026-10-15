# Scraping Ecosystem & Tool Selection Guide

Curated from modern web scraping best practices and `edwardtay/awesome-scrapers`.

## Tool Selection Matrix

| Scenario / Goal | Recommended Tool | Why |
| :--- | :--- | :--- |
| **Download images from single page / article** | `image_scraper.py` (Fast/Auto) | Lightweight, zero-setup, handles `srcset`, `data-src`, size/dim filters. |
| **Protected / Cloudflare / Turnstile pages** | `image_scraper.py --engine scrapling` or Scrapling CLI | Bypasses Cloudflare Turnstile and TLS fingerprint blocks out of the box. |
| **SPA / Infinite scroll / React / Vue** | `image_scraper.py --engine playwright --scroll-count N` | Headless Chromium executes JS, triggers hydration and intersection observers. |
| **Major platform albums & galleries** (Twitter/X, Reddit, Instagram, Pixiv, ArtStation) | `gallery-dl` | Purpose-built extractors for 100+ sites, resolves authenticated full-res originals. |
| **Video / Multi-format multimedia** | `yt-dlp` | Industry standard for videos, audio, and animated media from 1,000+ sites. |
| **High-concurrency bulk scraping** | `curl_cffi` + `selectolax` | 10-30x faster than BeautifulSoup, impersonates Chrome/Safari JA3/JA4 TLS fingerprints. |

---

## 1. `gallery-dl` vs Generic Scrapers

When scraping popular platforms (social media, image boards, portfolio sites), generic HTML scrapers often only get low-resolution thumbnails or get blocked by dynamic API rate limits. `gallery-dl` uses site-specific reverse-engineered API clients to fetch pristine uncompressed originals.

### Supported Domains (Highlights)
- **Social**: Twitter/X, Instagram, Reddit, Tumblr, Pinterest, Threads
- **Art & Portfolios**: ArtStation, DeviantArt, Pixiv, Behance, Cara
- **Image Hosts**: Imgur, Flickr, Danbooru, Gelbooru, CoHost

### Quick Usage
```bash
# Download entire album/profile
gallery-dl "https://twitter.com/user/media"

# Dump direct URLs only
gallery-dl -g "https://imgur.com/a/album_id"

# Filter by image resolution or date
gallery-dl --filter "width >= 1920" "https://reddit.com/r/wallpapers"
```

---

## 2. Anti-Detection & Stealth Strategies

Sites that block basic Python requests (`requests` or `urllib`) usually do so via:

1. **User-Agent & Header Checks**: Missing `Sec-Ch-Ua`, `Sec-Fetch-Dest`, or `Referer` headers.
   - *Fix*: `image_scraper.py` sends realistic Chrome headers and sets `Referer` matching origin.
2. **TLS / JA3 / HTTP2 Fingerprinting**: Python's OpenSSL cipher suite reveals a non-browser client.
   - *Fix*: Use `curl_cffi` with `impersonate="chrome131"` or `scrapling`.
3. **Behavioral & Turnstile Challenges**: Cloudflare interstitial / Turnstile JS challenge.
   - *Fix*: `scrapling extract stealthy-fetch "https://target.com" --solve-cloudflare`
4. **IP Rate Limiting**:
   - *Fix*: Pass `--proxy "http://user:pass@host:port"` to rotate residential or datacenter proxies.

---

## 3. High-Throughput Pipelines

When building programmatic crawlers that process tens of thousands of pages:

```python
# Ultra-fast parser: selectolax (Lexbor engine)
from selectolax.parser import HTMLParser
from curl_cffi import requests

resp = requests.get("https://example.com", impersonate="chrome131")
tree = HTMLParser(resp.text)

image_urls = []
for node in tree.css("img"):
    src = node.attributes.get("data-src") or node.attributes.get("src")
    if src:
        image_urls.append(src)
```
