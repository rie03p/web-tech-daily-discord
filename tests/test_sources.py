from __future__ import annotations

import unittest

from app.sources import SOURCES


class SourceTests(unittest.TestCase):
    def test_repaired_source_feed_urls(self):
        source_by_id = {source["id"]: source for source in SOURCES}

        self.assertEqual(source_by_id["google-cloud"]["url"], "https://docs.cloud.google.com/feeds/gcp-release-notes.xml")
        self.assertEqual(source_by_id["openai"]["url"], "https://github.com/openai/openai-python/releases.atom")

