from langgraph.graph import END

from deal_hunter.graph.state import DealHunterState


def route_after_search(state: DealHunterState) -> str:
    if not state.get("search_results"):
        return END
    if state.get("is_interactive", True):
        return "confirmer"
    return "auto_confirm"
