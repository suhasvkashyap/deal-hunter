import json
from decimal import Decimal
from pathlib import Path

from deal_hunter.models import Perk, PricePoint, Product
from deal_hunter.search.base import SearchClient


class MockSearchClient(SearchClient):
    def __init__(self, mock_data_dir: Path):
        self.mock_data_dir = mock_data_dir

    def _find_mock_file(self, query: str, retailer: str) -> Path | None:
        query_slug = query.lower().replace(" ", "_")
        for pattern in [
            f"{retailer}_{query_slug}.json",
            f"{retailer}_*.json",
        ]:
            matches = list(self.mock_data_dir.glob(pattern))
            if matches:
                return matches[0]
        return None

    def search_products(self, query: str, retailer: str) -> list[Product]:
        mock_file = self._find_mock_file(query, retailer)
        if not mock_file:
            return []

        data = json.loads(mock_file.read_text())
        products = []
        for item in data.get("products", []):
            products.append(
                Product(
                    retailer=item["retailer"],
                    title=item["title"],
                    url=item["url"],
                    sku=item.get("sku"),
                    image_url=item.get("image_url"),
                )
            )
        return products

    def get_product_details(self, product: Product) -> tuple[PricePoint, list[Perk]]:
        mock_file = self._find_mock_file("", product.retailer)
        if not mock_file:
            return (
                PricePoint(product_id=product.id, price=Decimal("0"), in_stock=False),
                [],
            )

        data = json.loads(mock_file.read_text())
        for item in data.get("products", []):
            if item.get("sku") == product.sku or item["title"] == product.title:
                price = PricePoint(
                    product_id=product.id,
                    price=Decimal(str(item["price"])),
                    currency=item.get("currency", "USD"),
                    in_stock=item.get("in_stock", True),
                    shipping=item.get("shipping"),
                )
                perks = [
                    Perk(
                        product_id=product.id,
                        category=p["category"],
                        description=p["description"],
                        value=p.get("value"),
                    )
                    for p in item.get("perks", [])
                ]
                return price, perks

        return (
            PricePoint(product_id=product.id, price=Decimal("0"), in_stock=False),
            [],
        )
