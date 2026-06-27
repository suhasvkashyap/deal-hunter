import threading
import uuid

import gradio as gr

from deal_hunter.config import Settings
from deal_hunter.graph.builder import build_graph
from deal_hunter.llm.provider import get_llm
from deal_hunter.search.mock_client import MockSearchClient
from deal_hunter.search.serpapi_client import SerpAPISearchClient
from deal_hunter.storage.history import PriceHistory
from deal_hunter.trace import TraceLog

settings = Settings()


def run_agent(query: str, history: list[dict], trace_output: str):
    if not query.strip():
        yield history, ""
        return

    trace = TraceLog()
    history = history + [{"role": "user", "content": query}]
    history.append({"role": "assistant", "content": "_Searching..._"})
    yield history, ""

    if settings.should_use_mock:
        client = MockSearchClient(settings.MOCK_DATA_DIR)
        trace.log("System", "Using **mock data** (set SERPAPI_KEY for live search)")
    else:
        client = SerpAPISearchClient(settings.SERPAPI_KEY)
        trace.log("System", "Using **SerpAPI** for live search")

    llm = get_llm(settings)
    price_history = PriceHistory(settings.DB_PATH)

    graph = build_graph(client, llm, settings.OUTPUT_DIR, price_history, trace=trace)

    thread_id = f"web-{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": thread_id}}
    initial_state = {
        "query": query,
        "retailers": settings.retailer_list,
        "is_interactive": False,
        "search_results": [],
        "errors": [],
    }

    trace.log("System", f"Agent started — LLM: `{settings.LLM_MODEL}` via `{settings.LLM_PROVIDER}`")
    yield history, trace.render()

    result_state = {}
    done = threading.Event()

    def _run():
        nonlocal result_state
        try:
            for event in graph.stream(initial_state, config, stream_mode="updates"):
                result_state.update(event)
        except Exception as e:
            trace.log("System", f"Error: {e}")
        done.set()

    t = threading.Thread(target=_run, daemon=True)
    t.start()

    prev_len = 0
    while not done.is_set():
        done.wait(timeout=0.3)
        if len(trace.entries) > prev_len:
            prev_len = len(trace.entries)
            history[-1] = {"role": "assistant", "content": "_Agents working..._"}
            yield history, trace.render()

    final = graph.get_state(config)
    report = final.values.get("report_markdown", "No results found.")
    errors = final.values.get("errors", [])

    if errors:
        trace.log("System", f"Completed with {len(errors)} warning(s)")
    else:
        trace.log("System", "All agents completed successfully")

    history[-1] = {"role": "assistant", "content": report}
    yield history, trace.render()


CSS = """
.trace-panel {font-size: 13px !important; line-height: 1.6 !important;}
"""

with gr.Blocks(title="Deal Hunter") as app:
    gr.Markdown(
        "# Deal Hunter — AI Price Comparison Agent\n"
        "Type a product to compare prices across Amazon, Costco, Walmart, and Best Buy."
    )

    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(
                height=600,
                placeholder="Type a product, e.g. 'Bosch 500 series dishwasher'",
            )
            msg = gr.Textbox(
                placeholder="What product do you want to compare?",
                show_label=False,
                container=False,
            )

        with gr.Column(scale=2):
            gr.Markdown("### Agent Activity")
            trace_box = gr.Markdown(
                value="*Waiting for a query...*",
                elem_classes=["trace-panel"],
            )

    msg.submit(
        fn=run_agent,
        inputs=[msg, chatbot, trace_box],
        outputs=[chatbot, trace_box],
    ).then(lambda: "", outputs=msg)


def main():
    app.launch(server_name="0.0.0.0", server_port=7860, theme=gr.themes.Soft(primary_hue="red"), css=CSS)


if __name__ == "__main__":
    main()
