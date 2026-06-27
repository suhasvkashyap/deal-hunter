from decimal import Decimal
from pathlib import Path

from deal_hunter.models import Perk, PricePoint, Product
from deal_hunter.reporting.markdown import build_report
from deal_hunter.search.mock_client import MockSearchClient

MOCK_DIR = Path(__file__).parent.parent / "mock_data"


def test_build_report_contains_table():
    product = Product(retailer="amazon", title="Bosch 500", url="https://amazon.com/dp/123", sku="SHP65CM5N")
    price = PricePoint(product_id=product.id, price=Decimal("899.99"), shipping="Free shipping")
    perk = Perk(product_id=product.id, category="warranty", description="1-year warranty", value="Included")

    report = build_report("Bosch dishwasher", [product], [price], [perk], "Test summary.")

    assert "# Deal Hunter Report" in report
    assert "899.99" in report
    assert "Warranty" in report
    assert "Test summary." in report


def test_report_with_multiple_retailers():
    client = MockSearchClient(MOCK_DIR)

    products = []
    prices = []
    perks = []
    for retailer in ["amazon", "costco"]:
        found = client.search_products("bosch dishwasher", retailer)
        if found:
            p = found[0]
            products.append(p)
            price, perk_list = client.get_product_details(p)
            prices.append(price)
            perks.extend(perk_list)

    report = build_report("Bosch dishwasher", products, prices, perks, "Multi-retailer comparison.")

    assert "Amazon" in report
    assert "Costco" in report
