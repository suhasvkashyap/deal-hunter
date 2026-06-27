import operator
from typing import Annotated, TypedDict

from deal_hunter.models import Perk, PricePoint, Product


class DealHunterState(TypedDict):
    query: str
    retailers: list[str]

    search_results: Annotated[list[Product], operator.add]
    errors: Annotated[list[str], operator.add]

    confirmed_products: list[Product]
    prices: list[PricePoint]
    perks: list[Perk]
    report_markdown: str
    report_path: str

    is_interactive: bool
