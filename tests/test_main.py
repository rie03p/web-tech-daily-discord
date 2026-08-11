from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from app.main import summarize


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

