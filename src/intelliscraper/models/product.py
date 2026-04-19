from dataclasses import dataclass, field, asdict
from typing import Optional, List
from datetime import datetime


@dataclass
class Image:
    url: str
    alt_text: Optional[str] = None
    position: int = 0

    def to_dict(self):
        return asdict(self)


@dataclass
class Variant:
    name: str
    sku: Optional[str] = None
    price: Optional[float] = None
    inventory_quantity: int = 0
    weight: Optional[float] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class Product:
    name: str
    description: str = ""
    price: float = 0.0
    url: str = ""
    category: str = ""
    subcategory: str = ""
    images: List[Image] = field(default_factory=list)
    variants: List[Variant] = field(default_factory=list)
    rating: Optional[float] = None
    reviews_count: int = 0
    availability: str = "in_stock"
    tags: List[str] = field(default_factory=list)
    vendor: str = "Store"
    sku: Optional[str] = None
    weight: Optional[float] = None
    scraped_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self):
        return asdict(self)

    def __post_init__(self):
        if not self.images:
            self.images = []
        if not self.variants:
            self.variants = []
        if not self.tags:
            self.tags = []
