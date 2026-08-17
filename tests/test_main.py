from __future__ import annotations

import os
import unittest
from datetime import date
from unittest.mock import patch

from app.main import articles_for_period, discord_payload, post_to_discord, summarize


ARTICLE = {
    "source": "Example",
    "title": "Example update",
    "url": "https://example.com/update",
    "topics": ["Example"],
    "description": "An example update.",
}


class SummarizeTests(unittest.TestCase):
    @patch("app.main.request_json")
    def test_reads_text_from_raw_responses_api_output(self, request_json):
        request_json.return_value = {
            "output": [
                {"type": "reasoning", "summary": []},
                {"type": "message", "content": [{
                    "type": "output_text",
                    "text": '{"overview":"概要","items":[{"url":"https://example.com/update","summary":"要約"}]}'
                }]},
            ]
        }

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True):
            digest = summarize([ARTICLE])

        self.assertEqual(digest["overview"], "概要")
        self.assertEqual(digest["items"], [{**ARTICLE, "summary": "要約"}])


class DiscordTests(unittest.TestCase):
    @patch("app.main.request_json")
    def test_posts_with_user_agent(self, request_json):
        with patch.dict(os.environ, {"DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/1/token"}, clear=True):
            post_to_discord({"content": "test"})

        request_json.assert_called_once_with(
            "https://discord.com/api/webhooks/1/token?wait=true",
            {"content": "test"},
            {"User-Agent": "web-tech-daily-discord/0.1 (+https://github.com/rie03p/web-tech-daily-discord)"},
        )

    def test_groups_items_by_source(self):
        payload = discord_payload({"overview": "概要", "items": [
            {**ARTICLE, "summary": "1件目"},
            {**ARTICLE, "title": "Another update", "url": "https://example.com/another", "summary": "2件目"},
        ]}, date(2026, 8, 5), date(2026, 8, 11))

        embed = payload["embeds"][0]
        self.assertEqual(embed["title"], "Web Tech Daily — 2026-08-05 – 2026-08-11 (JST)")
        self.assertEqual(embed["fields"][0]["name"], "Example（2件）")
        self.assertIn("1件目", embed["fields"][0]["value"])
        self.assertIn("2件目", embed["fields"][0]["value"])


class DigestSelectionTests(unittest.TestCase):
    def test_fallback_keeps_up_to_ten_items_regardless_of_source(self):
        articles = [
            {**ARTICLE, "title": f"AWS {number}", "source": "AWS"}
            for number in range(11)
        ]

        self.assertEqual([article["title"] for article in summarize(articles)["items"]], [f"AWS {number}" for number in range(10)])

    def test_selects_articles_in_requested_period(self):
        articles = [
            {**ARTICLE, "title": "Included", "published_at": "2026-08-05T00:00:00+09:00"},
            {**ARTICLE, "title": "Excluded", "published_at": "2026-08-04T23:59:59+09:00"},
        ]

        selected = articles_for_period(articles, date(2026, 8, 11), 7)

        self.assertEqual([article["title"] for article in selected], ["Included"])
