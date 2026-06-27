from datetime import datetime

from deal_hunter.models import Perk, PricePoint, Product


def build_report(
    query: str,
    products: list[Product],
    prices: list[PricePoint],
    perks: list[Perk],
    summary: str,
) -> str:
    price_by_id = {p.product_id: p for p in prices}
    perks_by_id: dict[str, list[Perk]] = {}
    for perk in perks:
        perks_by_id.setdefault(perk.product_id, []).append(perk)

    lines = [
        f"# Deal Hunter Report: {query}",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
        "",
        "## Price Comparison",
        "",
        "| Retailer | Product | Price | In Stock | Shipping |",
        "|----------|---------|-------|----------|----------|",
    ]

    for product in products:
        price = price_by_id.get(product.id)
        if price:
            stock = "Yes" if price.in_stock else "**No**"
            lines.append(
                f"| {product.retailer.title()} "
                f"| {product.title[:50]}{'...' if len(product.title) > 50 else ''} "
                f"| ${price.price} "
                f"| {stock} "
                f"| {price.shipping or 'N/A'} |"
            )

    lines.extend(["", "## Perks and Extras", ""])

    perk_categories = set()
    for perk_list in perks_by_id.values():
        for perk in perk_list:
            perk_categories.add(perk.category)
    perk_categories_sorted = sorted(perk_categories)

    if perk_categories_sorted:
        header = "| Retailer | " + " | ".join(c.title() for c in perk_categories_sorted) + " |"
        separator = "|----------| " + " | ".join("---" for _ in perk_categories_sorted) + " |"
        lines.append(header)
        lines.append(separator)

        for product in products:
            product_perks = perks_by_id.get(product.id, [])
            perk_map = {p.category: p for p in product_perks}
            cols = []
            for cat in perk_categories_sorted:
                perk = perk_map.get(cat)
                cols.append(perk.value or perk.description if perk else "-")
            lines.append(f"| {product.retailer.title()} | " + " | ".join(cols) + " |")

    lines.extend(["", "## Analysis", "", summary, ""])

    for product in products:
        lines.append(f"- [{product.retailer.title()}: {product.title[:60]}]({product.url})")

    lines.append("")
    return "\n".join(lines)
