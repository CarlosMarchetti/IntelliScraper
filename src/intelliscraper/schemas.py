from datetime import datetime
from typing import Any, Optional, Union
from pydantic import BaseModel, Field


class Product(BaseModel):
    name: str = Field(..., description="Product name")
    price: Optional[float] = Field(None, description="Product price")
    url: Optional[str] = Field(None, description="Product URL")
    image_url: Optional[str] = Field(None, description="Product image URL")
    description: Optional[str] = Field(None, description="Product description")
    rating: Optional[float] = Field(None, description="Product rating (0-5)")
    availability: Optional[str] = Field(None, description="Product availability status")
    raw_data: dict = Field(default_factory=dict, description="Raw extracted data")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Example Product",
                "price": 29.99,
                "url": "https://example.com/product",
                "rating": 4.5,
                "availability": "In Stock"
            }
        }


class ScraperResponse(BaseModel):
    success: bool
    data: Union[list[dict[str, Any]], list[Product]]
    url: str
    timestamp: datetime = Field(default_factory=datetime.now)
    error: Optional[str] = None
    items_count: int = 0
    duration_ms: float = 0.0

    def __init__(self, **data):
        super().__init__(**data)
        if self.items_count == 0 and self.data:
            self.items_count = len(self.data)


class ScrapedElement(BaseModel):
    selector: str
    content: str
    attributes: dict = Field(default_factory=dict)


class ExtractedData(BaseModel):
    url: str
    elements: list[ScrapedElement] = Field(default_factory=list)
    text_content: str = ""
    timestamp: datetime = Field(default_factory=datetime.now)


class PageMetadata(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    keywords: Optional[str] = None
    og_image: Optional[str] = None
    og_title: Optional[str] = None
    canonical_url: Optional[str] = None
    language: Optional[str] = None
    status_code: int = 200
