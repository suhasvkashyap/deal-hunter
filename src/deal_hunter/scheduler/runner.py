from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from rich.console import Console

from deal_hunter.config import Settings

console = Console()


def _run_agent(query: str, settings: Settings):
    from deal_hunter.graph.builder import build_graph
    from deal_hunter.llm.provider import get_llm
    from deal_hunter.search.mock_client import MockSearchClient
    from deal_hunter.search.serpapi_client import SerpAPISearchClient
    from deal_hunter.storage.history import PriceHistory

    if settings.should_use_mock:
        client = MockSearchClient(settings.MOCK_DATA_DIR)
    else:
        client = SerpAPISearchClient(settings.SERPAPI_KEY)

    llm = get_llm(settings)
    history = PriceHistory(settings.DB_PATH)
    graph = build_graph(client, llm, settings.OUTPUT_DIR, history)

    config = {"configurable": {"thread_id": f"scheduled-{query}"}}
    initial_state = {
        "query": query,
        "retailers": settings.retailer_list,
        "is_interactive": False,
        "search_results": [],
        "errors": [],
    }

    console.print(f"\n[bold yellow]Scheduled run:[/bold yellow] {query}")
    for _event in graph.stream(initial_state, config, stream_mode="updates"):
        pass


def run_on_schedule(cron_expression: str, query: str, settings: Settings) -> None:
    parts = cron_expression.split()
    if len(parts) != 5:
        console.print(f"[red]Invalid cron expression: {cron_expression}[/red]")
        console.print("Expected format: minute hour day_of_month month day_of_week")
        return

    trigger = CronTrigger.from_crontab(cron_expression)
    scheduler = BlockingScheduler()
    scheduler.add_job(_run_agent, trigger, args=[query, settings])

    console.print(f"[bold green]Scheduled:[/bold green] '{query}' with cron '{cron_expression}'")
    console.print("Press Ctrl+C to stop.\n")

    try:
        scheduler.start()
    except KeyboardInterrupt:
        console.print("\n[yellow]Scheduler stopped.[/yellow]")
