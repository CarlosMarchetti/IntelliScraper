import re
from typing import Optional, List
from urllib.parse import urljoin, urlparse
import json


class URLHelper:
    @staticmethod
    def is_absolute(url: str) -> bool:
        return bool(urlparse(url).scheme)

    @staticmethod
    def make_absolute(base_url: str, relative_url: str) -> str:
        if URLHelper.is_absolute(relative_url):
            return relative_url
        return urljoin(base_url, relative_url)

    @staticmethod
    def extract_domain(url: str) -> str:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    @staticmethod
    def normalize_url(url: str) -> str:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"


class TextHelper:
    @staticmethod
    def clean_text(text: str) -> str:
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    @staticmethod
    def extract_numbers(text: str) -> List[float]:
        matches = re.findall(r'\d+\.?\d*', text)
        return [float(m) for m in matches]

    @staticmethod
    def extract_emails(text: str) -> List[str]:
        return re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)

    @staticmethod
    def extract_phones(text: str) -> List[str]:
        return re.findall(r'\b(?:\+?1[-.]?)?(?:\(?([0-9]{3})\)?[-. ]?)?([0-9]{3})[-. ]?([0-9]{4})\b', text)

    @staticmethod
    def slugify(text: str) -> str:
        text = re.sub(r'[^\w\s-]', '', text.lower())
        return re.sub(r'[-\s]+', '-', text).strip('-')


class JSONHelper:
    @staticmethod
    def safe_json_dumps(obj, indent: int = 2, default: Optional[callable] = None) -> str:
        def json_serializer(o):
            if hasattr(o, 'isoformat'):
                return o.isoformat()
            if default:
                return default(o)
            return str(o)
        
        return json.dumps(obj, indent=indent, default=json_serializer)

    @staticmethod
    def safe_json_loads(json_str: str) -> Optional[dict]:
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return None


class DataProcessor:
    @staticmethod
    def deduplicate(items: List[dict], key: str) -> List[dict]:
        seen = set()
        result = []
        for item in items:
            value = item.get(key)
            if value not in seen:
                seen.add(value)
                result.append(item)
        return result

    @staticmethod
    def filter_by_field(items: List[dict], field: str, value: any) -> List[dict]:
        return [item for item in items if item.get(field) == value]

    @staticmethod
    def extract_field(items: List[dict], field: str) -> List[any]:
        return [item.get(field) for item in items if field in item]

    @staticmethod
    def group_by_field(items: List[dict], field: str) -> dict[any, List[dict]]:
        grouped = {}
        for item in items:
            key = item.get(field)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(item)
        return grouped

    @staticmethod
    def merge_dicts(items: List[dict]) -> dict:
        result = {}
        for item in items:
            result.update(item)
        return result
