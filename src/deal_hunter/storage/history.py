import sqlite3
from decimal import Decimal
from pathlib import Path

from deal_hunter.models import Perk, PricePoint, Product


class PriceHistory:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS products (
                    id TEXT PRIMARY KEY,
                    retailer TEXT NOT NULL,
                    title TEXT NOT NULL,
                    url TEXT,
                    sku TEXT,
                    image_url TEXT
                );
                CREATE TABLE IF NOT EXISTS price_points (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id TEXT NOT NULL,
                    price REAL NOT NULL,
                    currency TEXT DEFAULT 'USD',
                    in_stock INTEGER DEFAULT 1,
                    timestamp TEXT NOT NULL,
                    shipping TEXT,
                    FOREIGN KEY (product_id) REFERENCES products(id)
                );
                CREATE TABLE IF NOT EXISTS perks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT NOT NULL,
                    value TEXT,
                    FOREIGN KEY (product_id) REFERENCES products(id)
                );
            """)

    def save_price(self, product: Product, price: PricePoint, perks: list[Perk]) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO products (id, retailer, title, url, sku, image_url) VALUES (?, ?, ?, ?, ?, ?)",
                (product.id, product.retailer, product.title, product.url, product.sku, product.image_url),
            )
            conn.execute(
                "INSERT INTO price_points (product_id, price, currency, in_stock, timestamp, shipping) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    price.product_id,
                    float(price.price),
                    price.currency,
                    int(price.in_stock),
                    price.timestamp.isoformat(),
                    price.shipping,
                ),
            )
            for perk in perks:
                conn.execute(
                    "INSERT INTO perks (product_id, category, description, value) VALUES (?, ?, ?, ?)",
                    (perk.product_id, perk.category, perk.description, perk.value),
                )

    def get_latest_price(self, product_id: str) -> PricePoint | None:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT product_id, price, currency, in_stock, timestamp, shipping "
                "FROM price_points WHERE product_id = ? ORDER BY timestamp DESC LIMIT 1",
                (product_id,),
            ).fetchone()
            if not row:
                return None
            return PricePoint(
                product_id=row[0],
                price=Decimal(str(row[1])),
                currency=row[2],
                in_stock=bool(row[3]),
                shipping=row[5],
            )

    def get_price_history(self, product_id: str, limit: int = 10) -> list[PricePoint]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT product_id, price, currency, in_stock, timestamp, shipping "
                "FROM price_points WHERE product_id = ? ORDER BY timestamp DESC LIMIT ?",
                (product_id, limit),
            ).fetchall()
            return [
                PricePoint(
                    product_id=row[0],
                    price=Decimal(str(row[1])),
                    currency=row[2],
                    in_stock=bool(row[3]),
                    shipping=row[5],
                )
                for row in rows
            ]
