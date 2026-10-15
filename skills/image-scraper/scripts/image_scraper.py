#!/usr/bin/env python3
"""
Modern High-Performance Image Scraper & Downloader
Inspired by sananth12/ImageScraper and curated with modern scraping best practices
from edwardtay/awesome-scrapers (stealth, lazy-loading resolution, async I/O, deduplication).
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import mimetypes
import os
import re
import sys
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import httpx
from bs4 import BeautifulSoup

# Optional PIL for image dimension filtering
try:
    from PIL import Image
    import io
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".avif", ".bmp", ".ico", ".tiff"
}

LAZY_ATTRIBUTES = [
    "data-original",
    "data-high-res-src",
    "data-src",
    "data-lazy-src",
    "data-lazy",
    "data-url",
    "data-zoom-src",
    "data-full-src",
    "data-large-file",
    "src",
]

SRCSET_ATTRIBUTES = [
    "srcset",
    "data-srcset",
    "data-lazy-srcset",
]


@dataclass
class ScrapedImage:
    url: str
    source_tag: str = "img"
    attribute: str = "src"
    alt_text: str = ""
    width_hint: Optional[int] = None
    file_bytes: Optional[bytes] = None
    content_type: str = ""
    sha256: str = ""
    local_path: Optional[str] = None
    saved_size: int = 0
    dimensions: Optional[Tuple[int, int]] = None


def parse_srcset(srcset_val: str, base_url: str) -> List[Tuple[str, int]]:
    """
    Parse an HTML srcset attribute into a list of (absolute_url, score) pairs.
    Scores width descriptor (e.g. 1920w -> 1920) or density (e.g. 2x -> 2000).
    """
    candidates = []
    # Split by comma that is preceded by descriptor or whitespace
    parts = re.split(r",\s*(?=[^\s]+)", srcset_val.strip())
    for part in parts:
        part = part.strip()
        if not part:
            continue
        tokens = part.split()
        if not tokens:
            continue
        raw_url = tokens[0]
        abs_url = urllib.parse.urljoin(base_url, raw_url)
        score = 1
        if len(tokens) > 1:
            desc = tokens[1].lower()
            if desc.endswith("w"):
                try:
                    score = int(desc[:-1])
                except ValueError:
                    score = 1
            elif desc.endswith("x"):
                try:
                    score = int(float(desc[:-1]) * 1000)
                except ValueError:
                    score = 1
        candidates.append((abs_url, score))
    # Sort highest score first
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates


def extract_css_background_urls(style_str: str, base_url: str) -> List[str]:
    """Extract URLs from CSS inline style declarations like background: url(...)."""
    urls = []
    matches = re.findall(r"url\(\s*['\"]?([^'\"\)]+)['\"]?\s*\)", style_str, re.IGNORECASE)
    for m in matches:
        m = m.strip()
        if m and not m.startswith("data:"):
            urls.append(urllib.parse.urljoin(base_url, m))
    return urls


def sanitize_filename(name: str, max_len: int = 120) -> str:
    """Sanitize string for safe filesystem usage on Windows/Linux/macOS."""
    # Replace illegal filesystem chars
    clean = re.sub(r'[\\/*?:"<>|]', "_", name)
    clean = re.sub(r"\s+", "_", clean).strip("._")
    if not clean:
        clean = "image"
    if len(clean) > max_len:
        base, ext = os.path.splitext(clean)
        clean = base[: max_len - len(ext)] + ext
    return clean


class ModernImageScraper:
    def __init__(
        self,
        base_url: str,
        save_dir: Optional[str] = None,
        max_images: Optional[int] = None,
        formats: Optional[List[str]] = None,
        min_filesize: int = 0,
        max_filesize: int = 0,
        min_width: int = 0,
        min_height: int = 0,
        filename_pattern: Optional[str] = None,
        concurrency: int = 8,
        timeout: int = 20,
        proxy: Optional[str] = None,
        reverse: bool = False,
        engine: str = "auto",
        scroll_count: int = 2,
        dedup: bool = True,
        user_agent: str = DEFAULT_USER_AGENT,
        extra_headers: Optional[Dict[str, str]] = None,
    ):
        self.base_url = base_url.strip()
        if not self.base_url.startswith(("http://", "https://")):
            self.base_url = "https://" + self.base_url

        domain = urllib.parse.urlparse(self.base_url).netloc.replace(":", "_")
        self.save_dir = Path(save_dir) if save_dir else Path(f"images_{domain}")
        self.max_images = max_images
        self.formats = [f.lower().lstrip(".") for f in formats] if formats else None
        self.min_filesize = min_filesize
        self.max_filesize = max_filesize
        self.min_width = min_width
        self.min_height = min_height
        self.pattern = re.compile(filename_pattern) if filename_pattern else None
        self.concurrency = concurrency
        self.timeout = timeout
        self.proxy = proxy
        self.reverse = reverse
        self.engine = engine.lower()
        self.scroll_count = scroll_count
        self.dedup = dedup

        self.headers = {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Sec-Ch-Ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
        }
        if extra_headers:
            self.headers.update(extra_headers)

        self.seen_urls: Set[str] = set()
        self.seen_hashes: Set[str] = set()

    async def fetch_html_fast(self) -> str:
        """Fetch HTML using httpx."""
        async with httpx.AsyncClient(
            headers=self.headers,
            proxy=self.proxy,
            timeout=self.timeout,
            follow_redirects=True,
            verify=False,
        ) as client:
            resp = await client.get(self.base_url)
            resp.raise_for_status()
            return resp.text

    async def fetch_html_playwright(self) -> str:
        """Fetch HTML using Playwright headless browser with dynamic scrolling."""
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
            )
            context = await browser.new_context(
                user_agent=self.headers["User-Agent"],
                viewport={"width": 1920, "height": 1080},
                ignore_https_errors=True,
            )
            page = await context.new_page()
            await page.goto(self.base_url, wait_until="domcontentloaded", timeout=self.timeout * 1000)

            # Scroll to trigger lazy loading
            for _ in range(self.scroll_count):
                await page.evaluate("window.scrollBy(0, window.innerHeight * 1.5)")
                await asyncio.sleep(0.8)

            content = await page.content()
            await browser.close()
            return content

    def fetch_html_scrapling(self) -> str:
        """Fetch HTML using Scrapling CLI or module."""
        import shutil
        import subprocess

        scrapling_bin = shutil.which("scrapling")
        if not scrapling_bin:
            raise RuntimeError("scrapling binary not found on PATH")

        cmd = [scrapling_bin, "extract", "fetch", self.base_url, "temp_scrapling.html", "--network-idle"]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout + 15)
        if proc.returncode != 0 and not os.path.exists("temp_scrapling.html"):
            raise RuntimeError(f"Scrapling fetch failed: {proc.stderr}")

        try:
            with open("temp_scrapling.html", "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            return content
        finally:
            if os.path.exists("temp_scrapling.html"):
                os.remove("temp_scrapling.html")

    async def get_page_html(self) -> str:
        """Execute selected fetch engine."""
        if self.engine == "fast":
            return await self.fetch_html_fast()
        elif self.engine == "playwright":
            return await self.fetch_html_playwright()
        elif self.engine == "scrapling":
            return self.fetch_html_scrapling()
        else:
            # Auto: try fast first, check image count, fallback to browser if needed
            try:
                html = await self.fetch_html_fast()
                soup = BeautifulSoup(html, "html.parser")
                img_tags = soup.find_all(["img", "picture", "source"])
                if len(img_tags) > 2:
                    return html
            except Exception:
                pass

            # Try Playwright
            try:
                return await self.fetch_html_playwright()
            except Exception:
                # Fallback to fast
                return await self.fetch_html_fast()

    def discover_images(self, html: str) -> List[ScrapedImage]:
        """
        Inspect HTML tree and extract all candidate image URLs using
        deep heuristics (srcset, lazy data-attributes, CSS background, meta tags, schema.org).
        """
        soup = BeautifulSoup(html, "html.parser")
        images: List[ScrapedImage] = []

        def add_candidate(url: str, tag: str, attr: str, alt: str = "", score: int = 1):
            if not url or url.startswith("data:") or url.startswith("javascript:"):
                return
            abs_url = urllib.parse.urljoin(self.base_url, url.strip())
            # Clean unwanted hash/fragment
            abs_url, _ = urllib.parse.urldefrag(abs_url)

            # Apply filename/URL regex filter if set
            if self.pattern and not self.pattern.search(abs_url):
                return

            # Apply format extension filter if already discernible from URL path
            parsed = urllib.parse.urlparse(abs_url)
            ext = os.path.splitext(parsed.path)[1].lower()
            if ext and self.formats and ext.lstrip(".") not in self.formats:
                return

            if abs_url not in self.seen_urls:
                self.seen_urls.add(abs_url)
                images.append(
                    ScrapedImage(
                        url=abs_url,
                        source_tag=tag,
                        attribute=attr,
                        alt_text=alt,
                        width_hint=score,
                    )
                )

        # 1. <img> tags (lazy attributes + src + srcset)
        for img in soup.find_all("img"):
            alt = img.get("alt", "")
            # Check srcset first (usually highest resolution)
            found_srcset = False
            for src_attr in SRCSET_ATTRIBUTES:
                if img.get(src_attr):
                    candidates = parse_srcset(img[src_attr], self.base_url)
                    if candidates:
                        best_url, score = candidates[0]
                        add_candidate(best_url, "img", src_attr, alt, score=score)
                        found_srcset = True
                        break

            # Check lazy loading and standard attributes
            for attr in LAZY_ATTRIBUTES:
                val = img.get(attr)
                if val:
                    add_candidate(val, "img", attr, alt)
                    break

            # Inline style background on <img>
            if img.get("style"):
                for bg_url in extract_css_background_urls(img["style"], self.base_url):
                    add_candidate(bg_url, "img", "style", alt)

        # 2. <picture><source> elements
        for picture in soup.find_all("picture"):
            for source in picture.find_all("source"):
                for src_attr in SRCSET_ATTRIBUTES:
                    if source.get(src_attr):
                        candidates = parse_srcset(source[src_attr], self.base_url)
                        if candidates:
                            best_url, score = candidates[0]
                            add_candidate(best_url, "source", src_attr, score=score)
                            break

        # 3. Direct gallery links: <a href="...image.jpg">
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            parsed = urllib.parse.urlparse(href)
            ext = os.path.splitext(parsed.path)[1].lower()
            if ext in IMAGE_EXTENSIONS:
                add_candidate(href, "a", "href")

        # 4. Background images on containers (div, section, header, etc.)
        for el in soup.find_all(style=True):
            if el.name not in ["img"]:
                style = el.get("style", "")
                if "url(" in style.lower():
                    for bg_url in extract_css_background_urls(style, self.base_url):
                        add_candidate(bg_url, el.name, "style")

        # 5. OpenGraph & Twitter meta images
        for meta in soup.find_all("meta"):
            prop = meta.get("property", "").lower()
            name = meta.get("name", "").lower()
            content = meta.get("content", "").strip()
            if prop in ["og:image", "og:image:secure_url"] or name in [
                "twitter:image",
                "twitter:image:src",
            ]:
                if content:
                    add_candidate(content, "meta", prop or name)

        # 6. JSON-LD ImageObject schema
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
                self._extract_jsonld_images(data, add_candidate)
            except Exception:
                pass

        if self.reverse:
            images.reverse()

        if self.max_images and self.max_images > 0:
            images = images[: self.max_images]

        return images

    def _extract_jsonld_images(self, data: Any, add_fn: Any):
        """Recursively traverse JSON-LD object for image URLs."""
        if isinstance(data, dict):
            for k, v in data.items():
                if k in ["image", "thumbnailUrl", "contentUrl"]:
                    if isinstance(v, str):
                        add_fn(v, "json-ld", k)
                    elif isinstance(v, list):
                        for item in v:
                            if isinstance(item, str):
                                add_fn(item, "json-ld", k)
                            elif isinstance(item, dict) and "url" in item:
                                add_fn(item["url"], "json-ld", k)
                    elif isinstance(v, dict) and "url" in v:
                        add_fn(v["url"], "json-ld", k)
                else:
                    self._extract_jsonld_images(v, add_fn)
        elif isinstance(data, list):
            for item in data:
                self._extract_jsonld_images(item, add_fn)

    async def download_image(
        self, client: httpx.AsyncClient, img: ScrapedImage, semaphore: asyncio.Semaphore
    ) -> Optional[ScrapedImage]:
        """Download one image, check format, filesize, deduplication, and dimensions."""
        async with semaphore:
            try:
                headers = self.headers.copy()
                headers["Referer"] = self.base_url
                headers["Sec-Fetch-Dest"] = "image"
                headers["Sec-Fetch-Mode"] = "no-cors"

                resp = await client.get(img.url, headers=headers)
                if resp.status_code >= 400:
                    return None

                data = resp.content
                size = len(data)

                # Filesize limits
                if self.min_filesize > 0 and size < self.min_filesize:
                    return None
                if self.max_filesize > 0 and size > self.max_filesize:
                    return None

                # Hash deduplication
                sha256 = hashlib.sha256(data).hexdigest()
                if self.dedup:
                    if sha256 in self.seen_hashes:
                        return None
                    self.seen_hashes.add(sha256)

                img.sha256 = sha256
                img.file_bytes = data
                img.saved_size = size
                content_type = resp.headers.get("content-type", "").split(";")[0].strip().lower()
                img.content_type = content_type

                # Determine extension
                parsed = urllib.parse.urlparse(img.url)
                ext = os.path.splitext(parsed.path)[1].lower()
                if not ext or len(ext) > 5:
                    guessed = mimetypes.guess_extension(content_type)
                    ext = guessed if guessed else ".jpg"

                if ext == ".jpeg":
                    ext = ".jpg"

                # Check format filter
                if self.formats and ext.lstrip(".") not in self.formats:
                    return None

                # Dimension check via PIL if requested
                dims = None
                if HAS_PIL and (self.min_width > 0 or self.min_height > 0):
                    try:
                        pil_img = Image.open(io.BytesIO(data))
                        dims = pil_img.size
                        img.dimensions = dims
                        if self.min_width > 0 and dims[0] < self.min_width:
                            return None
                        if self.min_height > 0 and dims[1] < self.min_height:
                            return None
                    except Exception:
                        # Non-decodable or SVG
                        if ext not in [".svg"]:
                            return None

                # Generate clean filename
                raw_name = Path(parsed.path).name or f"image_{sha256[:10]}"
                base_name = os.path.splitext(raw_name)[0]
                clean_name = sanitize_filename(base_name) + ext
                save_file = self.save_dir / clean_name

                # Avoid collisions
                counter = 1
                while save_file.exists():
                    save_file = self.save_dir / f"{sanitize_filename(base_name)}_{counter}{ext}"
                    counter += 1

                self.save_dir.mkdir(parents=True, exist_ok=True)
                save_file.write_bytes(data)
                img.local_path = str(save_file)
                # Free memory
                img.file_bytes = None
                return img

            except Exception:
                return None

    async def run(self, dump_urls: bool = False, json_output: bool = False) -> List[ScrapedImage]:
        """Main execution flow."""
        html = await self.get_page_html()
        candidates = self.discover_images(html)

        if dump_urls:
            if json_output:
                out = [{"url": c.url, "tag": c.source_tag, "attr": c.attribute, "alt": c.alt_text} for c in candidates]
                print(json.dumps(out, indent=2))
            else:
                for c in candidates:
                    print(c.url)
            return candidates

        # Download images concurrently
        semaphore = asyncio.Semaphore(self.concurrency)
        async with httpx.AsyncClient(
            proxy=self.proxy,
            timeout=self.timeout,
            follow_redirects=True,
            verify=False,
        ) as client:
            tasks = [self.download_image(client, img, semaphore) for img in candidates]
            results = await asyncio.gather(*tasks)

        saved = [r for r in results if r is not None and r.local_path]

        if json_output:
            out = [
                {
                    "url": s.url,
                    "local_path": s.local_path,
                    "size_bytes": s.saved_size,
                    "sha256": s.sha256,
                    "content_type": s.content_type,
                    "dimensions": s.dimensions,
                }
                for s in saved
            ]
            print(json.dumps(out, indent=2))
        else:
            print(f"Scraped and saved {len(saved)} images to: {self.save_dir.resolve()}")
            for s in saved:
                dim_str = f" ({s.dimensions[0]}x{s.dimensions[1]})" if s.dimensions else ""
                print(f"  ✓ {Path(s.local_path).name} - {s.saved_size / 1024:.1f} KB{dim_str}")

        return saved


def main():
    parser = argparse.ArgumentParser(
        description="High-performance modern image scraper and downloader."
    )
    parser.add_argument("url", help="Target webpage URL")
    parser.add_argument("-s", "--save-dir", help="Directory where images will be saved")
    parser.add_argument("-m", "--max-images", type=int, help="Maximum number of images to download")
    parser.add_argument(
        "--formats",
        nargs="+",
        help="Specify allowed formats without dots (e.g. jpg png webp gif svg)",
    )
    parser.add_argument("--min-filesize", type=int, default=0, help="Minimum file size in bytes")
    parser.add_argument("--max-filesize", type=int, default=0, help="Maximum file size in bytes")
    parser.add_argument("--min-width", type=int, default=0, help="Minimum image width in pixels")
    parser.add_argument("--min-height", type=int, default=0, help="Minimum image height in pixels")
    parser.add_argument("--filename-pattern", help="Regex pattern matching image URL or filename")
    parser.add_argument("--dump-urls", action="store_true", help="Print image URLs without downloading")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    parser.add_argument("-c", "--concurrency", type=int, default=8, help="Concurrent download workers")
    parser.add_argument("--timeout", type=int, default=20, help="Request timeout in seconds")
    parser.add_argument("--proxy", help="Proxy URL (e.g. http://127.0.0.1:8080)")
    parser.add_argument("--reverse", action="store_true", help="Process images in reverse order")
    parser.add_argument(
        "--engine",
        choices=["auto", "fast", "scrapling", "playwright"],
        default="auto",
        help="Page extraction engine",
    )
    parser.add_argument(
        "--scroll-count",
        type=int,
        default=2,
        help="Number of scroll iterations for dynamic pages",
    )
    parser.add_argument("--no-dedup", action="store_true", help="Disable SHA-256 deduplication")

    args = parser.parse_args()

    scraper = ModernImageScraper(
        base_url=args.url,
        save_dir=args.save_dir,
        max_images=args.max_images,
        formats=args.formats,
        min_filesize=args.min_filesize,
        max_filesize=args.max_filesize,
        min_width=args.min_width,
        min_height=args.min_height,
        filename_pattern=args.filename_pattern,
        concurrency=args.concurrency,
        timeout=args.timeout,
        proxy=args.proxy,
        reverse=args.reverse,
        engine=args.engine,
        scroll_count=args.scroll_count,
        dedup=not args.no_dedup,
    )

    asyncio.run(scraper.run(dump_urls=args.dump_urls, json_output=args.json))


if __name__ == "__main__":
    main()
