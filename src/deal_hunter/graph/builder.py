from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.graph import END, START, StateGraph

from deal_hunter.graph.edges import route_after_search
from deal_hunter.graph.nodes.analyzer import make_analyzer_node
from deal_hunter.graph.nodes.confirmer import auto_confirm, confirmer
from deal_hunter.graph.nodes.reporter import make_reporter_node
from deal_hunter.graph.nodes.searcher import make_searcher_node
from deal_hunter.graph.state import DealHunterState
from deal_hunter.search.base import SearchClient
from deal_hunter.storage.history import PriceHistory

if TYPE_CHECKING:
    from deal_hunter.trace import TraceLog


def build_graph(
    search_client: SearchClient,
    llm: ChatOpenAI,
    output_dir: Path,
    history: PriceHistory | None = None,
    trace: TraceLog | None = None,
):
    builder = StateGraph(DealHunterState)

    builder.add_node("searcher", make_searcher_node(search_client, trace=trace))
    builder.add_node("confirmer", confirmer)
    builder.add_node("auto_confirm", auto_confirm)
    builder.add_node("analyzer", make_analyzer_node(search_client, history, trace=trace))
    builder.add_node("reporter", make_reporter_node(llm, output_dir, trace=trace))

    builder.add_edge(START, "searcher")
    builder.add_conditional_edges("searcher", route_after_search)
    builder.add_edge("confirmer", "analyzer")
    builder.add_edge("auto_confirm", "analyzer")
    builder.add_edge("analyzer", "reporter")
    builder.add_edge("reporter", END)

    serde = JsonPlusSerializer().with_msgpack_allowlist(["deal_hunter.models"])
    checkpointer = MemorySaver(serde=serde)
    return builder.compile(checkpointer=checkpointer)
