from langgraph.types import Command
from rich.console import Console

from deal_hunter.cli import parse_args
from deal_hunter.config import Settings
from deal_hunter.graph.builder import build_graph
from deal_hunter.llm.provider import get_llm
from deal_hunter.search.mock_client import MockSearchClient
from deal_hunter.search.serpapi_client import SerpAPISearchClient
from deal_hunter.storage.history import PriceHistory

console = Console()


def main():
    args = parse_args()
    settings = Settings()

    if args.mock:
        settings.USE_MOCK_DATA = True
    if args.output_dir:
        settings.OUTPUT_DIR = args.output_dir

    if args.schedule:
        from deal_hunter.scheduler.runner import run_on_schedule

        run_on_schedule(args.schedule, args.query, settings)
        return

    if settings.should_use_mock:
        client = MockSearchClient(settings.MOCK_DATA_DIR)
        console.print("[dim]Using mock data (set SERPAPI_KEY for live search)[/dim]")
    else:
        client = SerpAPISearchClient(settings.SERPAPI_KEY)
        console.print("[dim]Using SerpAPI for live search[/dim]")

    llm = get_llm(settings)
    history = PriceHistory(settings.DB_PATH)
    interactive = not args.non_interactive

    graph = build_graph(client, llm, settings.OUTPUT_DIR, history)

    thread_id = "cli-session"
    config = {"configurable": {"thread_id": thread_id}}
    initial_state = {
        "query": args.query,
        "retailers": settings.retailer_list,
        "is_interactive": interactive,
        "search_results": [],
        "errors": [],
    }

    console.print(f"\n[bold]Deal Hunter[/bold] - AI Price Comparison Agent")
    console.print(f"Provider: [cyan]{settings.LLM_PROVIDER}[/cyan] | Model: [cyan]{settings.LLM_MODEL}[/cyan]")

    for event in graph.stream(initial_state, config, stream_mode="updates"):
        pass

    state = graph.get_state(config)
    if state.next:
        prompt = state.tasks[0].interrupts[0].value if state.tasks else "Select products: "
        console.print(prompt)
        selection = input().strip()
        for event in graph.stream(Command(resume=selection), config, stream_mode="updates"):
            pass

    final_state = graph.get_state(config)
    errors = final_state.values.get("errors", [])
    if errors:
        console.print("\n[yellow]Warnings:[/yellow]")
        for error in errors:
            console.print(f"  - {error}")


if __name__ == "__main__":
    main()
