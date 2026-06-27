from datetime import datetime


class TraceLog:
    def __init__(self):
        self.entries: list[tuple[str, str, str]] = []

    def log(self, agent: str, message: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.entries.append((ts, agent, message))

    def clear(self):
        self.entries.clear()

    def render(self) -> str:
        lines = []
        for ts, agent, message in self.entries:
            lines.append(f"[{ts}] **{agent}** — {message}")
        return "\n\n".join(lines)
