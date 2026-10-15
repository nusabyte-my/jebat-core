# Advanced Image Extraction Heuristics

Modern websites rarely serve original images in simple `<img src="...">` tags. Below are the precise rules and heuristics implemented in `image-scraper` to extract maximum resolution assets.

---

## 1. The Attribute Priority Waterfall

When inspecting an `<img>` or `<picture>` element, evaluate attributes in this order:

```
1. srcset / data-srcset (Parse candidates -> pick highest 'w' or 'x' descriptor)
2. data-high-res-src / data-zoom-src / data-full-src (E-commerce / zoom modals)
3. data-original (Standard lazy loader, e.g. jQuery lazyload)
4. data-src / data-lazy-src / data-lazy (Modern vanilla/IntersectionObserver)
5. data-url (Custom web components)
6. src (Fallback; often a 1x1 base64 GIF or low-res blurhash placeholder)
```

### Srcset Parsing Rule
A `srcset` value consists of comma-separated items:
`<url> <descriptor>`
- Width descriptor: `url 1920w` -> weight: `1920`
- Density descriptor: `url 2x` -> weight: `2000` (density 2x ≈ 2000 equivalent score)
- Always extract the candidate with the highest weight.

---

## 2. CDN High-Resolution Stripping Rules

Many CMS and CDN engines inject thumbnail sizing into the URL path or query parameters. You can transform these URLs to get unconstrained original assets:

### WordPress
WordPress creates resized thumbnails by appending geometry:
- Thumbnail: `https://example.com/wp-content/uploads/2026/01/hero-768x512.jpg`
- Original: Regex replace `-\d+x\d+(\.[a-zA-Z]+)$` with `\1`
- Becomes: `https://example.com/wp-content/uploads/2026/01/hero.jpg`

### Shopify
Shopify appends size tags right before the extension:
- Thumbnail: `https://cdn.shopify.com/s/files/.../product_300x300.jpg?v=123`
- Original: Regex replace `_(?:pico|icon|thumb|small|compact|medium|large|grande|\d+x\d+)(\.[a-zA-Z]+)` with `\1`

### Unsplash
- Resized: `https://images.unsplash.com/photo-xxx?w=400&auto=format&fit=crop&q=60`
- High-res: Remove `w=...` and set `q=100`, or remove sizing query parameters entirely.

### Cloudinary
- Resized: `https://res.cloudinary.com/demo/image/upload/w_300,h_200,c_crop/sample.jpg`
- Original: Remove transformation segment `/w_\d+,h_\d+[^/]*/` or replace with `/fl_lossy,q_auto/`

---

## 3. CSS Background Images

Many modern landing pages place hero images and card thumbnails in CSS `background-image` properties rather than `<img>` tags.

### Regex Extraction
Match any inline style or embedded stylesheet containing:
```regex
url\(\s*['"]?([^'"\)]+)['"]?\s*\)
```
- Discard matches starting with `data:` (inline SVGs/GIFs) unless specifically collecting base64 assets.
- Resolve relative paths against the document's `base_url`.

---

## 4. Meta Tags & Structured Data (JSON-LD)

For articles, blog posts, and product pages, OpenGraph and Schema.org metadata usually point directly to the curated hero image:

- `<meta property="og:image" content="...">`
- `<meta property="og:image:secure_url" content="...">`
- `<meta name="twitter:image" content="...">`
- `<script type="application/ld+json">`: Look for fields `image`, `thumbnailUrl`, `contentUrl`.

---

## 5. Deduplication & Quality Filtering

1. **Tracking Pixels & Icons**:
   - Filter out files under 2-3 KB (`--min-filesize 3000`) to avoid tracking pixels, analytics beacons, and spacer GIFs.
   - Filter out images smaller than 100x100px (`--min-width 100 --min-height 100`).
2. **Hash Deduplication**:
   - Compute SHA-256 on image bytes. If an image is reused across different sections or URLs, store only one copy.
