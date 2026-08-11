from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
import re
from xml.etree import ElementTree as ET


def strip_html(value: str | None) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", unescape(value or ""))).strip()


def parse_date(value: str) -> datetime:
    try:
        result = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return result.astimezone(timezone.utc)


def find_text(element: ET.Element, names: set[str]) -> str:
    for child in element:
        if child.tag.split("}")[-1] in names and child.text:
            return strip_html(child.text)
    return ""


def parse_feed(xml: bytes, source: dict) -> list[dict]:
    root = ET.fromstring(xml)
    is_atom = root.tag.split("}")[-1] == "feed"
    entries = [element for element in root.iter() if element.tag.split("}")[-1] == ("entry" if is_atom else "item")]
    articles = []
    for entry in entries:
        title = find_text(entry, {"title"})
        raw_date = find_text(entry, {"updated", "published"} if is_atom else {"pubDate", "date"})
        url = ""
        if is_atom:
            for link in entry:
                if link.tag.split("}")[-1] == "link" and link.attrib.get("href"):
                    url = link.attrib["href"]
                    break
        else:
            url = find_text(entry, {"link"})
        if not (title and url and raw_date):
            continue
        try:
            published_at = parse_date(raw_date)
        except (TypeError, ValueError):
            continue
        articles.append({
            "source": source["name"], "source_id": source["id"], "topics": source["topics"],
            "title": title, "url": url, "published_at": published_at.isoformat(),
            "description": find_text(entry, {"content"} if is_atom else {"description"}),
        })
    return articles
