from decimal import Decimal

from deal_hunter.models import Perk, PricePoint, Product


def test_product_id_is_deterministic():
    p1 = Product(retailer="amazon", title="Bosch 500", url="https://amazon.com/dp/123")
    p2 = Product(retailer="amazon", title="Bosch 500", url="https://amazon.com/dp/123")
    assert p1.id == p2.id


def test_product_id_differs_by_retailer():
    p1 = Product(retailer="amazon", title="Bosch 500", url="https://example.com")
    p2 = Product(retailer="costco", title="Bosch 500", url="https://example.com")
    assert p1.id != p2.id


def test_price_point_defaults():
    pp = PricePoint(product_id="abc", price=Decimal("899.99"))
    assert pp.currency == "USD"
    assert pp.in_stock is True
    assert pp.timestamp is not None


def test_perk_creation():
    perk = Perk(
        product_id="abc",
        category="installation",
        description="Free basic installation",
        value="Free",
    )
    assert perk.category == "installation"
    assert perk.value == "Free"
