from decimal import Decimal

from serpapi import GoogleSearch

from deal_hunter.models import Perk, PricePoint, Product
from deal_hunter.search.base import SearchClient

RETAILER_KEYWORDS = {
    "amazon": ["amazon"],
    "costco": ["costco"],
    "walmart": ["walmart"],
    "bestbuy": ["best buy", "bestbuy"],
}


class SerpAPISearchClient(SearchClient):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._cache: dict[str, list[dict]] = {}

    def _fetch_shopping_results(self, query: str) -> list[dict]:
        if query in self._cache:
            return self._cache[query]

        search = GoogleSearch(
            {
                "engine": "google_shopping",
                "q": query,
                "api_key": self.api_key,
                "num": 30,
                "gl": "us",
                "hl": "en",
            }
        )
        results = search.get_dict()
        items = results.get("shopping_results", [])
        self._cache[query] = items
        return items

    def _matches_retailer(self, item: dict, retailer: str) -> bool:
        source = (item.get("source") or "").lower()
        link = (item.get("link") or item.get("product_link") or "").lower()
        keywords = RETAILER_KEYWORDS.get(retailer, [retailer])
        return any(kw in source or kw in link for kw in keywords)

    def search_products(self, query: str, retailer: str) -> list[Product]:
        all_items = self._fetch_shopping_results(query)

        products = []
        for item in all_items:
            if not self._matches_retailer(item, retailer):
                continue
            link = item.get("link") or item.get("product_link") or ""
            products.append(
                Product(
                    retailer=retailer,
                    title=item.get("title", "Unknown"),
                    url=link,
                    sku=item.get("product_id"),
                    image_url=item.get("thumbnail"),
                )
            )
            if len(products) >= 3:
                break
        return products

    def get_product_details(self, product: Product) -> tuple[PricePoint, list[Perk]]:
        all_items = self._fetch_shopping_results(product.title)

        match = None
        for item in all_items:
            if self._matches_retailer(item, product.retailer):
                match = item
                break

        if not match:
            all_items = self._fetch_shopping_results(product.title)
            if all_items:
                for item in all_items:
                    if self._matches_retailer(item, product.retailer):
                        match = item
                        break

        if not match:
            return (
                PricePoint(product_id=product.id, price=Decimal("0"), in_stock=False),
                [],
            )

        price_str = match.get("extracted_price") or match.get("price", "0")
        if isinstance(price_str, str):
            price_str = price_str.replace("$", "").replace(",", "")
        try:
            price_val = Decimal(str(price_str))
        except Exception:
            price_val = Decimal("0")

        price = PricePoint(
            product_id=product.id,
            price=price_val,
            currency="USD",
            in_stock=True,
            shipping=match.get("delivery"),
        )

        perks = []
        if match.get("delivery"):
            perks.append(
                Perk(
                    product_id=product.id,
                    category="shipping",
                    description=match["delivery"],
                )
            )
        if match.get("extensions"):
            for ext in match["extensions"]:
                perks.append(
                    Perk(
                        product_id=product.id,
                        category="info",
                        description=ext,
                    )
                )

        return price, perks
