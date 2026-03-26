"""
Fetch latest posts from industry leaders via RSS.
LinkedIn/Twitter posts are handled by the Claude Cowork scheduled prompt.
Falls back to latest_news.json if already populated today.
"""
from __future__ import annotations
import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

NEWS_PATH = Path(__file__).parent / "latest_news.json"

RSS_SOURCES = [
    # Anthropic has no public RSS — scraped via _scrape_anthropic() below
    {"person": "OpenAI",           "role": "AI research lab, makers of GPT & o1",      "platform": "Blog",       "color": "#10B981", "url": "https://openai.com/news",        "rss": "https://openai.com/news/rss.xml"},
    {"person": "Google DeepMind",  "role": "Google's AI research division",            "platform": "Blog",       "color": "#3B82F6", "url": "https://deepmind.google/blog",   "rss": "https://research.google/blog/rss/"},
    # Andrew Ng's The Batch has no public RSS — scraped via _scrape_the_batch() below
    {"person": "Andrej Karpathy",  "role": "AI researcher, ex-OpenAI, ex-Tesla AI",   "platform": "Blog",       "color": "#6B7280", "url": "https://karpathy.ai",            "rss": "https://karpathy.bearblog.dev/feed/"},
    {"person": "Peter Yang",       "role": "PM at Roblox, writes Product Compass",     "platform": "Substack",   "color": "#FF6719", "url": "https://www.productcompass.pm",  "rss": "https://www.productcompass.pm/feed"},
    {"person": "Ethan Mollick",    "role": "Wharton professor, AI in work & learning", "platform": "Substack",   "color": "#FF6719", "url": "https://www.oneusefulthing.org", "rss": "https://www.oneusefulthing.org/feed"},
    {"person": "Lenny Rachitsky",  "role": "Writes Lenny's Newsletter, top PM resource","platform": "Substack",  "color": "#FF6719", "url": "https://www.lennysnewsletter.com","rss": "https://www.lennysnewsletter.com/feed"},
    {"person": "Shreyas Doshi",    "role": "Product leader, ex-Stripe Twitter Yahoo",  "platform": "Substack",   "color": "#FF6719", "url": "https://shreyas.substack.com",   "rss": "https://shreyas.substack.com/feed"},
    {"person": "Swyx / Shawn Wang","role": "AI engineer, runs latent.space podcast",   "platform": "Blog",       "color": "#6B7280", "url": "https://www.latent.space",       "rss": "https://www.latent.space/feed"},
    {"person": "Julie Zhuo",       "role": "CPO, ex-VP Design Facebook, The Looking Glass","platform": "Medium", "color": "#000000","url": "https://medium.com/@joulee",     "rss": "https://medium.com/feed/@joulee"},
]

# Curated discovery pool — surfaces one new voice per day, rotating.
# People not already in the main reading list but relevant to a PM building AI agents.
DISCOVERY_POOL = [
    {"person": "Simon Willison",   "role": "Open-source dev, LLMs in practice (datasette, llm CLI)", "platform": "Blog",       "color": "#6B7280", "url": "https://simonwillison.net",              "why": "Best practitioner blog on using LLMs in real products — no hype, all signal."},
    {"person": "Chip Huyen",       "role": "ML Systems author, AI infra & production ML",             "platform": "Blog",       "color": "#6B7280", "url": "https://huyenchip.com/blog",             "why": "Bridges ML research and production — critical for AI agent infra decisions."},
    {"person": "François Chollet", "role": "Keras creator, ARC challenge, Google DeepMind",           "platform": "Twitter",    "color": "#000000", "url": "https://twitter.com/fchollet",           "why": "Contrarian AI thinker — pushes back on benchmark gaming and AGI hype."},
    {"person": "Mustafa Suleyman", "role": "CEO Microsoft AI, DeepMind co-founder, The Coming Wave", "platform": "Blog",       "color": "#6B7280", "url": "https://mustafasuleyman.com",            "why": "Enterprise AI strategy perspective from someone building at Microsoft scale."},
    {"person": "Teresa Torres",    "role": "Continuous discovery author, product coach",              "platform": "Blog",       "color": "#6B7280", "url": "https://www.producttalk.org/blog",       "why": "Best framework for evidence-driven product decisions — directly applicable to evals work."},
    {"person": "John Cutler",      "role": "Product clarity, Amplitude CPO advisor",                  "platform": "Substack",   "color": "#FF6719", "url": "https://cutlefish.substack.com",         "why": "Cuts through org complexity — great for PMs navigating cross-team work."},
    {"person": "Pawel Huryn",      "role": "Product frameworks, top PM Substack",                    "platform": "Substack",   "color": "#FF6719", "url": "https://www.productcompass.pm",          "why": "Practical PM frameworks with strong AI focus — popular among senior PMs."},
    {"person": "Dario Amodei",     "role": "CEO Anthropic, ex-OpenAI VP Research",                   "platform": "Blog",       "color": "#D97706", "url": "https://darioamodei.com",               "why": "Direct from the CEO building Claude — essential reading for AI strategy."},
    {"person": "Chris Olah",       "role": "AI interpretability researcher, Anthropic",               "platform": "Blog",       "color": "#D97706", "url": "https://colah.github.io",               "why": "Best explainer of how neural nets actually work — builds intuition for evals."},
    {"person": "Jeremy Howard",    "role": "fast.ai founder, practical deep learning",                "platform": "Blog",       "color": "#6B7280", "url": "https://www.fast.ai/posts.html",         "why": "Makes deep learning accessible — good antidote to research complexity."},
    {"person": "Wes Kao",          "role": "Maven co-founder, executive communication & management", "platform": "Newsletter", "color": "#8B5CF6", "url": "https://newsletter.weskao.com",          "why": "Best writing on managing up, executive presence, and stakeholder influence."},
    {"person": "Marty Cagan",      "role": "SVPG founder, Inspired & Empowered author",             "platform": "Blog",       "color": "#6B7280", "url": "https://www.svpg.com/articles",          "why": "The canonical product leadership framework — good calibration for senior PM work."},
    {"person": "Gibson Biddle",    "role": "Ex-CPO Netflix, product strategy essays",                 "platform": "Substack",   "color": "#FF6719", "url": "https://gibsonbiddle.substack.com",      "why": "Consumer-grade product thinking applied to enterprise — forces different framing."},
    {"person": "Clement Delangue", "role": "CEO Hugging Face, open-source AI ecosystem",             "platform": "LinkedIn",   "color": "#0A66C2", "url": "https://www.linkedin.com/in/clementdelangue", "why": "OSS AI model releases that will hit enterprise before you expect."},
    {"person": "Ilya Sutskever",   "role": "SSI founder, ex-OpenAI chief scientist",                 "platform": "Twitter",    "color": "#000000", "url": "https://twitter.com/ilyasut",            "why": "When he speaks about AI safety, it moves the industry."},
    {"person": "Amanda Askell",    "role": "Anthropic researcher, Claude RLHF & character",          "platform": "Twitter",    "color": "#D97706", "url": "https://twitter.com/amandaaskell",       "why": "Shapes how Claude reasons — directly relevant to agent behavior design."},
    {"person": "Alex Albert",      "role": "Head of developer relations at Anthropic",               "platform": "Twitter",    "color": "#D97706", "url": "https://twitter.com/alexalbert__",       "why": "First to surface what Claude Code users are actually building."},
    {"person": "Paul Graham",      "role": "YC founder, Hackers & Painters, startup essays",         "platform": "Blog",       "color": "#6B7280", "url": "https://paulgraham.com/articles.html",   "why": "Long-form thinking on building and working — especially good for clarity days."},
    {"person": "Cindy Alvarez",    "role": "UX research lead, Lean Customer Development author",     "platform": "Blog",       "color": "#6B7280", "url": "https://cindyalvarez.com",              "why": "Customer development rigour that pairs well with PM discovery work."},
    {"person": "Swami Sivasubramanian", "role": "VP of AI at AWS, enterprise AI services",          "platform": "LinkedIn",   "color": "#0A66C2", "url": "https://www.linkedin.com/in/swaminathansivasubramanian", "why": "AWS perspective on enterprise AI adoption — your customer's infrastructure layer."},
    {"person": "Rachel Thomas",    "role": "fast.ai co-founder, practical AI ethics",               "platform": "Blog",       "color": "#6B7280", "url": "https://rachel.fast.ai",                "why": "Grounded AI ethics thinking — useful for product decisions on agent trust."},
    {"person": "Dalton Caldwell",  "role": "YC managing director, SaaS & B2B product patterns",     "platform": "Twitter",    "color": "#000000", "url": "https://twitter.com/daltonc",            "why": "Pattern-matches B2B AI product mistakes before they become obvious."},
    {"person": "Sahil Lavingia",   "role": "Gumroad CEO, building-in-public practitioner",          "platform": "Twitter",    "color": "#000000", "url": "https://twitter.com/shl",               "why": "Radical transparency in product + business — good foil to big-company thinking."},
    {"person": "Jason Cohen",      "role": "WP Engine founder, long-form SaaS strategy essays",     "platform": "Blog",       "color": "#6B7280", "url": "https://longform.asmartbear.com",        "why": "Best essays on enterprise SaaS pricing, positioning, and product strategy."},
]

# These are handled by Claude Cowork (no reliable public RSS)
SEARCH_SOURCES = [
    {"person": "Matthew Simari",   "role": "Senior Director of Product at Instagram",  "platform": "LinkedIn",   "color": "#0A66C2"},
    {"person": "Steve Huynh",      "role": "Ex-Amazon Principal Engineer, A Life Engineered","platform": "YouTube","color": "#FF0000"},
    {"person": "Boris Cherny",     "role": "Founding engineer of Claude Code",          "platform": "LinkedIn",   "color": "#0A66C2"},
    {"person": "Yann LeCun",       "role": "Chief AI Scientist at Meta",               "platform": "LinkedIn",   "color": "#0A66C2"},
    {"person": "Kevin Weil",       "role": "CPO at OpenAI, ex-CPO Instagram",          "platform": "LinkedIn",   "color": "#0A66C2"},
    {"person": "Ami Vora",         "role": "CPO at Figma, ex-VP Product WhatsApp",     "platform": "LinkedIn",   "color": "#0A66C2"},
    {"person": "Harrison Chase",   "role": "CEO of LangChain, AI agents ecosystem",    "platform": "LinkedIn",   "color": "#0A66C2"},
    {"person": "Sam Altman",       "role": "CEO of OpenAI",                            "platform": "Blog",       "color": "#6B7280"},
    {"person": "Andrej Karpathy",  "role": "AI researcher, ex-OpenAI, ex-Tesla AI",   "platform": "Twitter",    "color": "#000000"},
]


def _scrape_anthropic() -> dict | None:
    """Scrape Anthropic's news page (no public RSS)."""
    import urllib.request, re
    try:
        req = urllib.request.Request(
            "https://www.anthropic.com/news",
            headers={"User-Agent": "Mozilla/5.0 Chrome/120"},
        )
        with urllib.request.urlopen(req, timeout=12) as r:
            body = r.read(200000).decode("utf-8", "ignore")
        pattern = (
            r'href=["\']?(/news/[a-z0-9\-]+)["\']?[^>]*>.*?'
            r'<time[^>]*>([^<]+)</time>.*?'
            r'<h\d[^>]*>([^<]+)</h\d>.*?'
            r'<p[^>]*>(.*?)(?:</p>|<a\s)'
        )
        m = re.search(pattern, body, re.DOTALL)
        if not m:
            return None
        slug, date_str, title, desc_html = m.groups()
        desc = re.sub(r"<[^>]+>", " ", desc_html)
        desc = re.sub(r"\s+", " ", desc).strip()[:280]
        try:
            from datetime import datetime
            pub = datetime.strptime(date_str.strip(), "%b %d, %Y").strftime("%Y-%m-%d")
        except Exception:
            pub = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return {
            "person": "Anthropic",
            "role": "AI safety company, makers of Claude",
            "platform": "Blog",
            "color": "#D97706",
            "title": title.strip(),
            "description": desc,
            "url": f"https://www.anthropic.com{slug}",
            "published": pub,
            "relevance": "",
        }
    except Exception:
        return None


def _scrape_the_batch() -> dict | None:
    """Scrape Andrew Ng's The Batch (no public RSS) — fetch listing then latest issue."""
    import urllib.request, re
    headers = {"User-Agent": "Mozilla/5.0 Chrome/120"}
    try:
        # Get listing page to find latest issue slug
        req = urllib.request.Request("https://www.deeplearning.ai/the-batch/", headers=headers)
        with urllib.request.urlopen(req, timeout=12) as r:
            listing = r.read(200000).decode("utf-8", "ignore")
        # Find highest issue number
        issue_nums = [int(n) for n in re.findall(r'the-batch/issue-(\d+)', listing)]
        if not issue_nums:
            return None
        latest = max(issue_nums)
        issue_url = f"https://www.deeplearning.ai/the-batch/issue-{latest}/"
        # Fetch the issue page for title + description + date
        req2 = urllib.request.Request(issue_url, headers=headers)
        with urllib.request.urlopen(req2, timeout=12) as r2:
            body = r2.read(30000).decode("utf-8", "ignore")
        title_m = re.search(r'<title>([^<|]+)', body)
        desc_m = re.search(r'og:description["\'][^>]*content=["\']([^"\']+)', body)
        date_m = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d+,?\s*\d{4}', body)
        title = title_m.group(1).strip() if title_m else f"The Batch Issue {latest}"
        desc = desc_m.group(1).strip()[:280] if desc_m else "Weekly AI news and insights from DeepLearning.AI."
        pub = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if date_m:
            try:
                from datetime import datetime as dt
                pub = dt.strptime(date_m.group(0), "%b %d, %Y").strftime("%Y-%m-%d")
            except Exception:
                pass
        return {
            "person": "Andrew Ng",
            "role": "AI pioneer, founder DeepLearning.AI, The Batch newsletter",
            "platform": "Newsletter",
            "color": "#8B5CF6",
            "title": title,
            "description": desc,
            "url": issue_url,
            "published": pub,
            "relevance": "",
        }
    except Exception:
        return None


def _fetch_rss(source: dict) -> dict | None:
    try:
        import feedparser
    except ImportError:
        return None
    try:
        feed = feedparser.parse(source["rss"])
        if not feed.entries:
            return None
        e = feed.entries[0]
        title = e.get("title", "")
        summary = e.get("summary", e.get("content", [{}])[0].get("value", ""))
        # Strip HTML tags from summary
        import re
        summary = re.sub(r"<[^>]+>", " ", summary).strip()
        summary = re.sub(r"\s+", " ", summary)[:280]
        link = e.get("link", source["url"])
        published = e.get("published", "")
        if published:
            from email.utils import parsedate_to_datetime
            try:
                published = parsedate_to_datetime(published).strftime("%Y-%m-%d")
            except Exception:
                published = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        else:
            published = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return {
            "person": source["person"],
            "role": source["role"],
            "platform": source["platform"],
            "color": source["color"],
            "title": title,
            "description": summary,
            "url": link,
            "published": published,
            "relevance": "",
        }
    except Exception:
        return None


def fetch_news() -> dict:
    """Fetch RSS sources; preserve any Claude-sourced items already in latest_news.json."""
    # Load existing file to preserve Claude Cowork items (LinkedIn/Twitter)
    existing: dict = {}
    if NEWS_PATH.exists():
        try:
            data = json.loads(NEWS_PATH.read_text())
            # Index by person name
            for item in data.get("items", []):
                existing[item["person"]] = item
        except Exception:
            pass

    items = []
    fetched_names: set[str] = set()

    # Scraped sources (no public RSS available)
    for fn, name in [(_scrape_anthropic, "Anthropic"), (_scrape_the_batch, "Andrew Ng")]:
        result = fn()
        if result:
            items.append(result)
        elif name in existing:
            items.append(existing[name])
        fetched_names.add(name)

    # RSS sources
    for source in RSS_SOURCES:
        fetched = _fetch_rss(source)
        if fetched:
            items.append(fetched)
        elif source["person"] in existing:
            items.append(existing[source["person"]])
        fetched_names.add(source["person"])

    # Preserve Claude Cowork items (LinkedIn/Twitter) not handled above
    for person, item in existing.items():
        if person not in fetched_names:
            items.append(item)

    # Sort by published date descending
    items.sort(key=lambda x: x.get("published", ""), reverse=True)

    # Pick one discovery suggestion for today (rotates daily, deterministic)
    today = datetime.now(timezone.utc).date()
    day_of_year = today.timetuple().tm_yday
    pick = DISCOVERY_POOL[day_of_year % len(DISCOVERY_POOL)]
    daily_pick = {
        "person": pick["person"],
        "role": pick["role"],
        "platform": pick["platform"],
        "color": pick["color"],
        "url": pick["url"],
        "why": pick["why"],
        "date": today.isoformat(),
    }

    return {
        "generated": datetime.now(timezone.utc).isoformat(),
        "items": items,
        "daily_pick": daily_pick,
    }


NEWS_DIR = Path(__file__).parent / "news"


def _replace_sentinel(html: str, start: str, end: str, content: str) -> str:
    import re
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    new_block = f"{start}\n{content}\n{end}"
    return pattern.sub(lambda _: new_block, html) if pattern.search(html) else html


def save_daily_snapshot(news: dict) -> None:
    """Save today's news to news/YYYY-MM-DD.json and prune files older than 30 days."""
    NEWS_DIR.mkdir(exist_ok=True)
    today = datetime.now(timezone.utc).date()
    snapshot = {"date": today.isoformat(), **news}
    path = NEWS_DIR / f"{today.isoformat()}.json"
    path.write_text(json.dumps(snapshot, indent=2, default=str))
    print(f"  ✓ news/{today.isoformat()}.json saved")
    cutoff = (today - timedelta(days=30)).isoformat()
    for f in NEWS_DIR.glob("*.json"):
        if f.stem < cutoff:
            f.unlink()


def build_history() -> list:
    """Load up to 14 daily snapshots, newest first."""
    if not NEWS_DIR.exists():
        return []
    history = []
    for f in sorted(NEWS_DIR.glob("*.json"), reverse=True)[:14]:
        try:
            history.append(json.loads(f.read_text()))
        except Exception:
            pass
    return history


def inject_into_html(news: dict, history: list) -> None:
    """Inject NEWS_DATA and HISTORY into index.html."""
    html_path = Path(__file__).parent / "index.html"
    if not html_path.exists():
        print("  ⚠ index.html not found — skipping")
        return
    html = html_path.read_text()
    html = _replace_sentinel(html, "/* NEWS_DATA_START */", "/* NEWS_DATA_END */",
                              f"const NEWS_DATA = {json.dumps(news, indent=2, default=str)};")
    html = _replace_sentinel(html, "/* HISTORY_START */", "/* HISTORY_END */",
                              f"const HISTORY = {json.dumps(history, indent=2, default=str)};")
    html_path.write_text(html)
    print(f"  ✓ index.html updated ({len(history)} days in history)")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    news = fetch_news()
    NEWS_PATH.write_text(json.dumps(news, indent=2, default=str))
    print(f"  ✓ latest_news.json saved ({len(news['items'])} items)")
    for item in news["items"]:
        print(f"    {item['platform']:12} {item['person']:25} {item.get('title','')[:60]}")
    if news.get("daily_pick"):
        p = news["daily_pick"]
        print(f"  ✦ Today's pick: {p['person']} ({p['platform']})")
    save_daily_snapshot(news)
    history = build_history()
    inject_into_html(news, history)
