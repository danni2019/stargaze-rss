from pathlib import Path

from stargaze_rss.feed import canonical_url, parse_feed
from stargaze_rss.pipeline import summarize_entries


def test_fictional_feed_produces_two_briefs():
    feed = Path(__file__).parents[1] / "examples/synthetic.rss"
    rows = summarize_entries(parse_feed(feed.read_bytes()))
    assert len(rows) == 2
    assert len(rows[0]["sources"]) == 2
    assert rows[0]["summary"] == "A fictional harbor added a second terminal this morning."


def test_json_entries_normalize_urls_and_strip_scripts():
    entries = parse_feed(b'[{"title":"Example","link":"/a#fragment","summary":"<script>hidden</script><p>Visible</p>"}]',
                         base_url="https://example.org/feed")
    assert entries[0]["url"] == "https://example.org/a"
    assert entries[0]["summary"] == "Visible"
    assert canonical_url("https://user@example.invalid/") == ""
