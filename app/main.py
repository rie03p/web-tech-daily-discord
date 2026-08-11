from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta
import json
import os
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from app.feed import parse_feed
from app.sources import SOURCES

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "data" / "state.json"
TOKYO = ZoneInfo("Asia/Tokyo")


def fetch_feed(source: dict) -> list[dict]:
    request = Request(source["url"], headers={"User-Agent": "web-tech-daily-discord/0.1 (+official-feed-monitor)"})
    with urlopen(request, timeout=30) as response:
        return parse_feed(response.read(), source)


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {"sent_urls": []}
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(exist_ok=True)
    temporary = STATE_PATH.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(STATE_PATH)


def fallback_digest(articles: list[dict]) -> dict:
    return {
        "overview": f"{len(articles)}件の公式アップデートを収集しました。",
        "items": [{**article, "summary": (article["description"] or "詳細は一次ソースをご確認ください。")[:280]} for article in limit_per_source(articles)],
    }


def request_json(url: str, payload: dict, headers: dict[str, str]) -> dict:
    request = Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json", **headers}, method="POST")
    try:
        with urlopen(request, timeout=60) as response:
            return json.loads(response.read())
    except HTTPError as error:
        detail = error.read().decode("utf-8", "replace")
        raise RuntimeError(f"HTTP {error.code} from {url}: {detail}") from error


def response_output_text(body: dict) -> str:
    """Extract text from a raw Responses API response."""
    parts = [
        content["text"]
        for item in body["output"]
        if item.get("type") == "message"
        for content in item.get("content", [])
        if content.get("type") == "output_text" and isinstance(content.get("text"), str)
    ]
    if not parts:
        raise KeyError("output_text")
    return "".join(parts)


def limit_per_source(articles: list[dict], per_source: int = 2, total: int = 10) -> list[dict]:
    selected, counts = [], {}
    for article in articles:
        source = article["source"]
        if counts.get(source, 0) >= per_source:
            continue
        selected.append(article)
        counts[source] = counts.get(source, 0) + 1
        if len(selected) == total:
            break
    return selected


def articles_for_period(articles: list[dict], end_date: date, days: int) -> list[dict]:
    start_date = end_date - timedelta(days=days - 1)
    return [
        article for article in articles
        if start_date <= datetime.fromisoformat(article["published_at"]).astimezone(TOKYO).date() <= end_date
    ]


def summarize(articles: list[dict]) -> dict:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or not articles:
        return fallback_digest(articles)
    candidates = [{key: article[key] for key in ("source", "title", "url", "topics")} | {"description": article["description"][:900]} for article in articles[:40]]
    prompt = """あなたはWeb系企業の技術ニュース編集者です。以下の公式アップデート候補から、実務で追う価値が高い最大10件を選び、日本語で要約してください。同じsourceからは最大2件までにしてください。破壊的変更、セキュリティ、料金、GA、主要な機能追加、重要な非推奨を優先します。URLは入力のものをそのまま使用し、推測や外部情報を加えません。

厳密に次のJSONだけを返してください: {"overview":"全体を一文で","items":[{"url":"入力URL","summary":"何が変わったか。なぜ重要か（120文字以内）"}]}

候補:
""" + json.dumps(candidates, ensure_ascii=False)
    body = request_json("https://api.openai.com/v1/responses", {
        "model": os.environ.get("OPENAI_MODEL", "gpt-5.6-luna"),
        "input": prompt,
        "max_output_tokens": 2500,
        "store": False,
    }, {"Authorization": f"Bearer {api_key}"})
    try:
        text = response_output_text(body)
        start, end = text.index("{"), text.rindex("}") + 1
        result = json.loads(text[start:end])
    except (KeyError, ValueError, json.JSONDecodeError) as error:
        raise RuntimeError("OpenAI response was not the expected JSON") from error
    article_by_url = {article["url"]: article for article in articles}
    selected = []
    for item in result.get("items", [])[:10]:
        article = article_by_url.get(item.get("url"))
        summary = item.get("summary")
        if article and isinstance(summary, str):
            selected.append({**article, "summary": summary[:700]})
    selected = limit_per_source(selected)
    return {"overview": str(result.get("overview", "")), "items": selected} if selected else fallback_digest(articles)


def discord_payload(digest: dict, start_date: date, end_date: date) -> dict:
    grouped = {}
    for item in digest["items"]:
        grouped.setdefault(item["source"], []).append(item)
    fields = [{
        "name": f"{source}（{len(items)}件）"[:256],
        "value": "\n\n".join(f"• {item['summary']}\n[一次ソースを開く]({item['url']})" for item in items)[:1024],
        "inline": False,
    } for source, items in grouped.items()]
    if not fields:
        fields = [{"name": "更新なし", "value": "監視している公式フィードには対象日の新着がありませんでした。", "inline": False}]
    period = end_date.isoformat() if start_date == end_date else f"{start_date.isoformat()} – {end_date.isoformat()}"
    return {"username": "Web Tech Daily", "embeds": [{
        "title": f"Web Tech Daily — {period} (JST)", "description": digest["overview"] or "期間中の公式アップデートです。",
        "color": 0x5865F2, "fields": fields, "footer": {"text": "Sources: official RSS / Atom feeds"},
    }]}


def post_to_discord(payload: dict) -> None:
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        raise RuntimeError("DISCORD_WEBHOOK_URL is required (use --dry-run to inspect without posting)")
    request_json(
        f"{webhook_url}{'&' if '?' in webhook_url else '?'}wait=true",
        payload,
        {"User-Agent": "web-tech-daily-discord/0.1 (+https://github.com/rie03p/web-tech-daily-discord)"},
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Send an official web-tech daily digest to Discord.")
    parser.add_argument("--dry-run", action="store_true", help="Discordへ投稿せず、生成payloadを表示します")
    parser.add_argument("--date", type=date.fromisoformat, default=datetime.now(TOKYO).date(), help="対象日（JST、YYYY-MM-DD）")
    parser.add_argument("--days", type=int, default=1, help="対象日を含めて遡る日数（既定: 1）")
    args = parser.parse_args()
    if args.days < 1:
        parser.error("--days must be at least 1")
    state = load_state()
    sent_urls = set(state["sent_urls"])
    articles, failures, successful_sources = [], [], 0
    for source in SOURCES:
        try:
            articles.extend(fetch_feed(source))
            successful_sources += 1
        except (URLError, ValueError, OSError) as error:
            failures.append(f"{source['name']}: {error}")
    if successful_sources == 0:
        raise RuntimeError("All configured feeds failed; refusing to send an empty digest")
    articles = articles_for_period(articles, args.date, args.days)
    if os.environ.get("INCLUDE_PREVIOUSLY_SENT") != "true":
        articles = [article for article in articles if article["url"] not in sent_urls]
    articles.sort(key=lambda article: article["published_at"], reverse=True)
    digest = summarize(articles)
    start_date = args.date - timedelta(days=args.days - 1)
    payload = discord_payload(digest, start_date, args.date)
    if args.dry_run:
        print(json.dumps({"start_date": start_date.isoformat(), "end_date": args.date.isoformat(), "articles": len(articles), "failures": failures, "payload": payload}, ensure_ascii=False, indent=2))
        return
    post_to_discord(payload)
    save_state({"sent_urls": list(dict.fromkeys([*state["sent_urls"], *(article["url"] for article in articles)]))[-3000:]})
    print(f"Posted {len(digest['items'])} item(s) for {start_date} through {args.date}. {len(failures)} source(s) failed.")
    for failure in failures:
        print(failure, file=sys.stderr)


if __name__ == "__main__":
    main()
