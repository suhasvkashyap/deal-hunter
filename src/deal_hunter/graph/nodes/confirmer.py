from langgraph.types import Command, interrupt

from deal_hunter.graph.state import DealHunterState
from deal_hunter.models import Product


def _format_product_list(products: list[Product]) -> str:
    lines = []
    for i, p in enumerate(products, 1):
        lines.append(f"  [{i}] ({p.retailer.upper()}) {p.title}")
        lines.append(f"      {p.url}")
    return "\n".join(lines)


def confirmer(state: DealHunterState) -> Command:
    products = state["search_results"]
    if not products:
        return Command(update={"confirmed_products": []})

    product_list = _format_product_list(products)
    prompt = (
        f"\nFound {len(products)} product(s):\n\n"
        f"{product_list}\n\n"
        "Enter the numbers of products to compare (e.g., 1,3,5) or 'all': "
    )

    selection = interrupt(prompt)

    if selection.strip().lower() == "all":
        return Command(update={"confirmed_products": products})

    try:
        indices = [int(x.strip()) - 1 for x in selection.split(",")]
        selected = [products[i] for i in indices if 0 <= i < len(products)]
    except (ValueError, IndexError):
        selected = products

    return Command(update={"confirmed_products": selected})


def auto_confirm(state: DealHunterState) -> dict:
    products = state["search_results"]
    seen_retailers: set[str] = set()
    selected = []
    for p in products:
        if p.retailer not in seen_retailers:
            seen_retailers.add(p.retailer)
            selected.append(p)

    return {"confirmed_products": selected}
