import argparse


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="deal-hunter",
        description="AI agent for comparing product prices across retail websites",
    )
    parser.add_argument(
        "query",
        help="Product to search for (e.g., 'Bosch 500 series dishwasher')",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Skip product confirmation (auto-select top results per retailer)",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Force mock data (no SerpAPI calls)",
    )
    parser.add_argument(
        "--schedule",
        type=str,
        default=None,
        metavar="CRON",
        help="Run on a cron schedule (e.g., '0 8 * * *' for daily at 8am)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory to write reports (default: from config)",
    )
    return parser.parse_args()
