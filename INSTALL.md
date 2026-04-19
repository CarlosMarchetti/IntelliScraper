# Installation Guide - IntelliScraper

## 📦 Install from PyPI (Recomendado)

```bash
pip install intelliscraper
```

Depois instale o navegador Chromium:

```bash
python -m playwright install chromium
```

---

## 🛠️ Install from Source (Desenvolvimento)

```bash
git clone https://github.com/yourusername/intelliscraper.git
cd intelliscraper
pip install -e .
python -m playwright install chromium
```

---

## 📋 Verificar Instalação

```python
from intelliscraper import IntelliScraper, ProductScraper

print("✅ IntelliScraper instalado com sucesso!")
```

---

## 🚀 Quick Start Após Instalação

```python
import asyncio
from intelliscraper import ProductScraper

async def main():
    async with ProductScraper(vendor_name="MyStore") as scraper:
        products = await scraper.scrape_products_from_page(
            url="https://example.com/products",
            product_selector=".product",
            name_selector=".name",
            price_selector=".price",
            category="Electronics",
            subcategory="Phones"
        )
        scraper.add_products(products)
        scraper.export_all_shopify_csv()

asyncio.run(main())
```

---

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'intelliscraper'"
```bash
pip install intelliscraper --upgrade
```

### "playwright is not installed"
```bash
playwright install chromium
```

### "Cannot find Chrome/Chromium"
```bash
playwright install --with-deps chromium
```

---

## 📚 Próximos Passos

Veja a documentação em `README.md` ou no repositório.
