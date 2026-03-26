"""
Bootstrap 7 days of news history from the current latest_news.json baseline.
Run once — after that, fetch_news.py saves each day's real snapshot automatically.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from fetch_news import DISCOVERY_POOL

NEWS_DIR = Path(__file__).parent / "news"
LATEST = Path(__file__).parent / "latest_news.json"


def generate_history(days: int = 7) -> None:
    if not LATEST.exists():
        print("  ✗ latest_news.json not found — run fetch_news.py first")
        return

    NEWS_DIR.mkdir(exist_ok=True)
    baseline = json.loads(LATEST.read_text())
    today = datetime.now(timezone.utc).date()

    for i in range(days):
        day = today - timedelta(days=i)
        date_str = day.isoformat()
        dest = NEWS_DIR / f"{date_str}.json"
        if dest.exists():
            print(f"  · {date_str}.json already exists, skipping")
            continue

        day_of_year = day.timetuple().tm_yday
        pick_src = DISCOVERY_POOL[day_of_year % len(DISCOVERY_POOL)]

        snapshot = {
            "date": date_str,
            "generated": datetime(day.year, day.month, day.day, 7, 0, 0, tzinfo=timezone.utc).isoformat(),
            "items": baseline.get("items", []),
            "daily_pick": {
                "person": pick_src["person"],
                "role": pick_src["role"],
                "platform": pick_src["platform"],
                "color": pick_src["color"],
                "url": pick_src["url"],
                "why": pick_src["why"],
                "date": date_str,
            },
        }
        dest.write_text(json.dumps(snapshot, indent=2, default=str))
        print(f"  ✓ {date_str}.json")


if __name__ == "__main__":
    generate_history()
    print("History bootstrap complete.")
