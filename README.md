# Daily product and AI news

One tab instead of fifteen. Every weekday morning, the latest from the people worth following.

---

## What this is

A feed that pulls RSS posts from a fixed list of product and AI thinkers, synthesizes them with Claude, and serves a clean static page. It updates itself Monday through Friday at 7am EST, so you get a fresh digest without having to check anything.

The problem it solves is simple: staying current without the context-switching. You open one URL, you see what's worth reading today, and you move on.

Live site: https://daily-product-news.vercel.app

---

## How it works

A GitHub Actions workflow runs every weekday morning. A Python script fetches the latest posts from each RSS source, passes them to Claude for synthesis, and commits `latest_news.json` and `index.html` back to the repo. Vercel picks up the commit and serves the updated page.

No database, no backend, no moving parts beyond that.

---

## Sources

| Voice | What they write about |
|---|---|
| Andrej Karpathy | AI research and engineering |
| Ethan Mollick | AI in work and education |
| Lenny Rachitsky | Product and growth |
| Shreyas Doshi | Product thinking and leadership |
| Julie Zhuo | Design and management |
| Swyx | AI for developers |
| Peter Yang | Consumer product and creator economy |
| OpenAI | Model releases and research |
| Google DeepMind | Research and product updates |

---

## Discovery pool

Each day the feed also surfaces one voice from a rotating list of about 24 people. These are writers and researchers worth knowing who don't always make the main list. One per day, rotating through the full set before repeating.

---

## Adding a source

Edit `RSS_SOURCES` in `fetch_news.py`. Add a dict with `name`, `url`, and `rss` fields. The next scheduled run will include it.

---

## Running locally

```
pip install -r requirements.txt
python fetch_news.py
```

This writes `latest_news.json` and `index.html` to the repo root. Open `index.html` in a browser to see the output.
