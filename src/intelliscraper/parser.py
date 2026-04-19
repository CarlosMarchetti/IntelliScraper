from typing import List, Optional, Dict, Any
from bs4 import BeautifulSoup
from intelliscraper.utils.logger import get_logger

logger = get_logger(__name__)


class HTMLParser:
    def __init__(self, html: str, parser: str = "html.parser"):
        self.soup = BeautifulSoup(html, parser)

    def extract_text(self, selector: Optional[str] = None) -> str:
        """Returns the text content for a selector, or the full page text if omitted."""
        if selector:
            element = self.soup.select_one(selector)
            return element.get_text(strip=True) if element else ""
        return self.soup.get_text(strip=True)

    def extract_elements(self, selector: str) -> List[Dict[str, Any]]:
        """Returns a list of dicts with tag, text and attributes for all matching elements."""
        return [
            {
                "tag": el.name,
                "text": el.get_text(strip=True),
                "attributes": dict(el.attrs),
            }
            for el in self.soup.select(selector)
        ]

    def extract_links(self, selector: str = "a") -> List[Dict[str, str]]:
        """Returns all links (href, text, title) matching the selector."""
        return [
            {
                "text": link.get_text(strip=True),
                "href": link.get("href", ""),
                "title": link.get("title", ""),
            }
            for link in self.soup.select(selector)
            if link.get("href")
        ]

    def extract_tables(self) -> List[List[List[str]]]:
        """Returns all tables as a 3D list: [table][row][cell]."""
        return [
            [
                [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
                for tr in table.find_all("tr")
            ]
            for table in self.soup.find_all("table")
        ]

    def extract_images(self, selector: str = "img") -> List[Dict[str, str]]:
        """Returns all images (src, alt, title, width, height) matching the selector."""
        return [
            {
                "src": img.get("src", ""),
                "alt": img.get("alt", ""),
                "title": img.get("title", ""),
                "width": img.get("width", ""),
                "height": img.get("height", ""),
            }
            for img in self.soup.select(selector)
            if img.get("src")
        ]

    def extract_metadata(self) -> Dict[str, str]:
        """
        Extracts common page metadata: title, description, keywords and Open Graph tags.
        Correctly handles both `name` and `property` attributes on <meta> tags.
        """
        metadata = {
            "title": "",
            "description": "",
            "keywords": "",
            "og_image": "",
            "og_title": "",
            "og_description": "",
            "og_url": "",
            "canonical_url": "",
            "language": "",
        }

        if title := self.soup.find("title"):
            metadata["title"] = title.get_text(strip=True)

        for meta in self.soup.find_all("meta"):
            # Standard meta tags use `name`; Open Graph uses `property`
            name = meta.get("name", "").lower()
            prop = meta.get("property", "").lower()
            content = meta.get("content", "")

            if name == "description":
                metadata["description"] = content
            elif name == "keywords":
                metadata["keywords"] = content
            elif prop == "og:image":
                metadata["og_image"] = content
            elif prop == "og:title":
                metadata["og_title"] = content
            elif prop == "og:description":
                metadata["og_description"] = content
            elif prop == "og:url":
                metadata["og_url"] = content

        if canonical := self.soup.find("link", {"rel": "canonical"}):
            metadata["canonical_url"] = canonical.get("href", "")

        if html_tag := self.soup.find("html"):
            metadata["language"] = html_tag.get("lang", "")

        return metadata

    def find_element(self, selector: str) -> Optional[Dict[str, Any]]:
        """Returns the first matching element as a dict, or None."""
        element = self.soup.select_one(selector)
        if not element:
            return None
        return {
            "tag": element.name,
            "text": element.get_text(strip=True),
            "attributes": dict(element.attrs),
        }

    def find_elements(self, selector: str) -> List[Dict[str, Any]]:
        """Returns all matching elements as a list of dicts."""
        return self.extract_elements(selector)

    def extract_by_xpath_style(self, **selectors) -> Dict[str, Any]:
        """
        Extracts multiple fields using keyword arguments as selector mappings.
        Append '::text' to a selector to get only the text value.

        Example:
            parser.extract_by_xpath_style(
                title="h1::text",
                links="a.product-link",
            )
        """
        results = {}
        for key, selector in selectors.items():
            try:
                if selector.endswith("::text"):
                    results[key] = self.extract_text(selector[:-7])
                else:
                    elements = self.extract_elements(selector)
                    results[key] = elements if elements else None
            except Exception as e:
                logger.warning(f"Error extracting '{key}' with selector '{selector}': {e}")
                results[key] = None
        return results