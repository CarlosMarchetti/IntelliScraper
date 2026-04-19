# IntelliScraper

Browser automation built on Playwright with stealth anti-detection baked in. No configuration required to get started.

```python
import asyncio
from intelliscraper import Scraper

async def main():
    async with Scraper() as scraper:
        await scraper.goto("https://example.com")
        print(await scraper.get_title())

asyncio.run(main())
```

---

## Installation

```bash
git clone https://github.com/CarlosMarchetti/IntelliScraper.git
cd IntelliScraper
pip install -r requirements.txt
playwright install chromium
```

Copy `.env.example` to `.env` and adjust if needed — defaults work out of the box.

Runnable examples are in the [`examples/`](examples/) folder.

---

## Usage

### Navigation

```python
async with Scraper(headless=False) as scraper:
    await scraper.goto("https://example.com")
    await scraper.goto("https://example.com", wait_until="networkidle")  # for SPAs
```

### Extracting data

```python
# Single element
title    = await scraper.get_text("h1")
href     = await scraper.get_attribute("a.primary", "href")

# Multiple elements
quotes   = await scraper.get_texts(".quote .text")
hrefs    = await scraper.get_attributes("a", "href")

# Full page
html     = await scraper.get_html()
soup     = await scraper.get_soup()   # returns HTMLParser
metadata = soup.extract_metadata()   # title, description, og_image, og_title, ...
links    = soup.extract_links()
tables   = soup.extract_tables()
```

### Interacting

```python
# fill() sets the value instantly; type() simulates real keystrokes
await scraper.fill("input[name='q']", "search term")
await scraper.type("input[name='q']", "search term")

await scraper.click("button[type='submit']")
await scraper.press("Enter")
await scraper.scroll(500)          # px down
await scraper.scroll_to_bottom()
```

### Waiting

```python
await scraper.wait(".results-container")          # waits for element to appear
await scraper.wait_hidden(".loading-spinner")     # waits for element to disappear
await scraper.wait_for_url("**/dashboard**")      # waits for URL to match a pattern
await scraper.sleep(2)
```

### Session persistence

Useful for sites that require login — authenticate once and reuse the session across runs.

```python
async with Scraper.with_session("session.json") as scraper:
    await scraper.goto("https://example.com")

    if await scraper.is_visible("a[href='/login']"):
        await scraper.goto("https://example.com/login")
        await scraper.fill("input[name='user']", "myuser")
        await scraper.fill("input[name='pass']", "mypass")
        await scraper.click("button[type='submit']")
        await scraper.wait_for_url("**/")
    
    # do your work — session is saved automatically on exit
```

Or manage it manually:

```python
async with Scraper() as scraper:
    await scraper.load_session("session.json")
    # ...
    await scraper.save_session("session.json")
```

### Intercepting network responses

Captures API responses as the page loads, without parsing HTML.

```python
products = []

async def on_response(response):
    if "/api/products" in response.url and response.status == 200:
        data = await response.json()
        products.extend(data.get("items", []))

async with Scraper() as scraper:
    await scraper.intercept_requests("**/**", on_response)
    await scraper.goto("https://example.com/shop")
    await scraper.sleep(3)

print(products)
```

### Screenshots

```python
await scraper.screenshot("debug.png")             # saved to ./screenshots/debug.png
await scraper.screenshot("step1.png", folder="runs/2026-01-01")
```

### Proxy & locale

```python
async with Scraper(
    headless=True,
    proxy="http://user:pass@host:8080",
    locale="en-US",
    timezone="America/New_York",
) as scraper:
    ...
```

---

## Configuration

All settings can be set via environment variables in `.env`:

| Variable              | Default   | Description                                          |
|-----------------------|-----------|------------------------------------------------------|
| `HEADLESS`            | `false`   | Run without a browser window                         |
| `TIMEOUT`             | `30000`   | Page load timeout in ms                              |
| `MAX_RETRIES`         | `3`       | Retry attempts for `goto()` and `click()`            |
| `RETRY_DELAY`         | `1.0`     | Base delay between retries in seconds                |
| `PROXY_URL`           | —         | Proxy URL, e.g. `http://user:pass@host:8080`         |
| `LOG_LEVEL`           | `WARNING` | `DEBUG`, `INFO`, `WARNING`, or `ERROR`               |
| `CACHE_ENABLED`       | `true`    | Enable response caching                              |
| `CACHE_TTL`           | `3600`    | Cache expiry in seconds                              |
| `RATE_LIMIT_REQUESTS` | `5`       | Max requests per window                              |
| `RATE_LIMIT_WINDOW`   | `60`      | Rate limit window in seconds                         |

---

## HTMLParser reference

`get_soup()` returns an `HTMLParser` instance:

```python
soup = await scraper.get_soup()

soup.extract_text("h1")                       # text of the first h1
soup.extract_elements("div.card")             # list of {tag, text, attributes}
soup.extract_links("nav a")                   # list of {text, href, title}
soup.extract_images("img.product")            # list of {src, alt, title, width, height}
soup.extract_tables()                         # 3D list [table][row][cell]
soup.extract_metadata()                       # title, description, og_*, canonical_url, language
soup.find_element("section.hero")             # first match as dict
soup.find_elements("section.hero")            # all matches as list

# Map multiple selectors in one call
soup.extract_by_xpath_style(
    title="h1::text",
    price=".price",
)
```

---

## Anti-detection

Every session automatically applies:

- `navigator.webdriver` removed and spoofed to `false`
- Playwright and Selenium property names hidden from `Object.keys`, `getOwnPropertyNames`, etc.
- Realistic browser plugins and MIME types injected
- `window.chrome.runtime` populated
- Canvas fingerprint noise applied per render
- WebGL vendor strings set to Intel
- Network RTT spoofed to a realistic value
- Consistent language headers between HTTP and JavaScript

---

## License

MIT
