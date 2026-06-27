from __future__ import annotations

from typing import TYPE_CHECKING

from rich.console import Console

from deal_hunter.graph.state import DealHunterState
from deal_hunter.models import Perk, PricePoint
from deal_hunter.search.base import SearchClient
from deal_hunter.storage.history import PriceHistory

if TYPE_CHECKING:
    from deal_hunter.trace import TraceLog

console = Console()


def make_analyzer_node(client: SearchClient, history: PriceHistory | None = None, trace: TraceLog | None = None):
    def analyzer(state: DealHunterState) -> dict:
        confirmed = state.get("confirmed_products", [])
        if not confirmed:
            return {"prices": [], "perks": []}

        all_prices: list[PricePoint] = []
        all_perks: list[Perk] = []

        console.print("\n[bold blue]Analyzing prices and perks...[/bold blue]")
        if trace:
            trace.log("Analyzer", f"Fetching prices for {len(confirmed)} product(s)")

        for product in confirmed:
            console.print(f"  Checking [cyan]{product.retailer}[/cyan] - {product.title[:60]}...", end=" ")
            if trace:
                trace.log("Analyzer", f"Checking {product.retailer}: {product.title[:50]}...")
            try:
                price, perks = client.get_product_details(product)
                all_prices.append(price)
                all_perks.extend(perks)

                if history:
                    history.save_price(product, price, perks)

                console.print(f"[green]${price.price}[/green]")
                if trace:
                    trace.log("Analyzer", f"{product.retailer}: **${price.price}** — {len(perks)} perk(s)")
            except Exception as e:
                console.print(f"[red]error: {e}[/red]")
                if trace:
                    trace.log("Analyzer", f"Error for {product.retailer}: {e}")

        if trace:
            trace.log("Analyzer", f"Analysis complete — {len(all_prices)} prices, {len(all_perks)} perks collected")

        return {"prices": all_prices, "perks": all_perks}

    return analyzer
