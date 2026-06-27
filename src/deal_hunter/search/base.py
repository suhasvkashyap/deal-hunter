from abc import ABC, abstractmethod

from deal_hunter.models import Perk, PricePoint, Product


class SearchClient(ABC):
    @abstractmethod
    def search_products(self, query: str, retailer: str) -> list[Product]:
        ...

    @abstractmethod
    def get_product_details(self, product: Product) -> tuple[PricePoint, list[Perk]]:
        ...
