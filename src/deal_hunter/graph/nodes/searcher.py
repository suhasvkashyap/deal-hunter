from __future__ import annotations

from typing import TYPE_CHECKING

from rich.console import Console

from deal_hunter.graph.state import DealHunterState
from deal_hunter.search.base import SearchClient

if TYPE_CHECKING:
    from deal_hunter.trace import TraceLog

console = Console()


def make_searcher_node(client: SearchClient, trace: TraceLog | None = None):
    def searcher(state: DealHunterState) -> dict:
        query = state["query"]
        retailers = state["retailers"]
        all_products = []
        errors = []

        console.print(f"\n[bold blue]Searching for:[/bold blue] {query}")
        if trace:
            trace.log("Searcher", f"Starting search for **{query}**")

        for retailer in retailers:
            console.print(f"  Searching [cyan]{retailer}[/cyan]...", end=" ")
            if trace:
                trace.log("Searcher", f"Querying {retailer}.com ...")
            try:
                products = client.search_products(query, retailer)
                all_products.extend(products)
                console.print(f"[green]found {len(products)} product(s)[/green]")
                if trace:
                    trace.log("Searcher", f"Found {len(products)} product(s) on {retailer}")
            except Exception as e:
                errors.append(f"{retailer}: {e}")
                console.print(f"[red]error: {e}[/red]")
                if trace:
                    trace.log("Searcher", f"Error on {retailer}: {e}")

        if trace:
            trace.log("Searcher", f"Search complete — {len(all_products)} total products found")

        return {"search_results": all_products, "errors": errors}

    return searcher
