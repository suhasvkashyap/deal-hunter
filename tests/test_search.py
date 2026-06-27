from pathlib import Path

from deal_hunter.search.mock_client import MockSearchClient

MOCK_DIR = Path(__file__).parent.parent / "mock_data"


def test_mock_client_finds_amazon_products():
    client = MockSearchClient(MOCK_DIR)
    products = client.search_products("bosch dishwasher", "amazon")
    assert len(products) == 2
    assert all(p.retailer == "amazon" for p in products)


def test_mock_client_finds_costco_products():
    client = MockSearchClient(MOCK_DIR)
    products = client.search_products("bosch dishwasher", "costco")
    assert len(products) == 2


def test_mock_client_gets_product_details():
    client = MockSearchClient(MOCK_DIR)
    products = client.search_products("bosch dishwasher", "costco")
    price, perks = client.get_product_details(products[0])
    assert price.price > 0
    assert len(perks) > 0
    categories = {p.category for p in perks}
    assert "installation" in categories
    assert "disposal" in categories


def test_mock_client_empty_for_unknown_retailer():
    client = MockSearchClient(MOCK_DIR)
    products = client.search_products("bosch dishwasher", "target")
    assert products == []
