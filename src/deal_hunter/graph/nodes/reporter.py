from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from langchain_openai import ChatOpenAI
from rich.console import Console
from rich.markdown import Markdown

from deal_hunter.graph.state import DealHunterState
from deal_hunter.reporting.markdown import build_report

if TYPE_CHECKING:
    from deal_hunter.trace import TraceLog

console = Console()

SYSTEM_PROMPT = """\
You are a consumer shopping advisor. Given product data from multiple retailers, \
write a concise comparison analysis. Focus on:

1. Price differences and which retailer offers the best deal
2. Non-obvious considerations that save or cost money:
   - Free installation vs paid installation
   - Free appliance disposal/haul-away vs extra fee
   - Extended warranty included vs purchased separately
   - Membership requirements (Costco) and their annual cost
   - Financing offers (0% APR)
   - Return policy differences (30 days vs 90 days)
   - Shipping speed differences
3. Stock availability issues
4. A clear recommendation with reasoning

Write in plain, direct language. Use bullet points. No fluff."""


def make_reporter_node(llm: ChatOpenAI, output_dir: Path, trace: TraceLog | None = None):
    def reporter(state: DealHunterState) -> dict:
        confirmed = state.get("confirmed_products", [])
        prices = state.get("prices", [])
        perks = state.get("perks", [])
        query = state["query"]

        if not confirmed or not prices:
            return {"report_markdown": "No products to compare.", "report_path": ""}

        product_data = _build_product_context(confirmed, prices, perks)

        console.print("\n[bold blue]Generating comparison analysis...[/bold blue]")
        if trace:
            trace.log("Reporter", "Sending product data to LLM for comparison analysis...")

        response = llm.invoke(
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Compare these products for the query '{query}':\n\n{product_data}"},
            ]
        )
        summary = response.content

        if trace:
            trace.log("Reporter", "LLM analysis received — building report")

        report = build_report(query, confirmed, prices, perks, summary)

        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = query.lower().replace(" ", "_")[:30]
        report_path = output_dir / f"{slug}_{timestamp}.md"
        report_path.write_text(report)

        console.print(f"\n[bold green]Report saved to:[/bold green] {report_path}")
        console.print()
        console.print(Markdown(report))

        if trace:
            trace.log("Reporter", f"Report saved to `{report_path}`")

        return {"report_markdown": report, "report_path": str(report_path)}

    return reporter


def _build_product_context(confirmed, prices, perks) -> str:
    price_by_id = {p.product_id: p for p in prices}
    perks_by_id: dict[str, list] = {}
    for perk in perks:
        perks_by_id.setdefault(perk.product_id, []).append(perk)

    lines = []
    for product in confirmed:
        price = price_by_id.get(product.id)
        product_perks = perks_by_id.get(product.id, [])

        lines.append(f"## {product.retailer.upper()}: {product.title}")
        lines.append(f"- URL: {product.url}")
        if price:
            lines.append(f"- Price: ${price.price} {price.currency}")
            lines.append(f"- In Stock: {'Yes' if price.in_stock else 'No'}")
            if price.shipping:
                lines.append(f"- Shipping: {price.shipping}")
        for perk in product_perks:
            lines.append(f"- {perk.category.title()}: {perk.description} ({perk.value or 'N/A'})")
        lines.append("")

    return "\n".join(lines)
