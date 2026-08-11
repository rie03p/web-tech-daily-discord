import unittest

from app.feed import parse_feed


class FeedTests(unittest.TestCase):
    source = {"id": "example", "name": "Example", "topics": []}

    def test_parses_rss_and_html_content(self):
        xml = b"<rss><channel><item><title>New &amp; improved</title><link>https://example.com/a</link><pubDate>Mon, 11 Aug 2026 00:30:00 GMT</pubDate><description>&lt;p&gt;Hello&lt;/p&gt;</description></item></channel></rss>"
        [item] = parse_feed(xml, self.source)
        self.assertEqual(item["title"], "New & improved")
        self.assertEqual(item["description"], "Hello")

    def test_parses_atom_link(self):
        xml = b'<feed><entry><title>Release</title><link href="https://example.com/r"/><updated>2026-08-11T10:00:00Z</updated><content>Notes</content></entry></feed>'
        [item] = parse_feed(xml, self.source)
        self.assertEqual(item["url"], "https://example.com/r")


if __name__ == "__main__":
    unittest.main()
