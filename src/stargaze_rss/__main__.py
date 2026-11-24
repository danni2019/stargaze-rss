import argparse
import json
from pathlib import Path

from httpx import HTTPError

from .feed import _MAX_FEED_BYTES, fetch_items, parse_feed
from .pipeline import summarize_entries


def main():
    parser = argparse.ArgumentParser(description="Read a feed and produce extractive news briefs.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--file", type=Path, help="local RSS, Atom, or JSON file")
    source.add_argument("--url", help="HTTP(S) feed URL")
    args = parser.parse_args()
    try:
        if args.file:
            with args.file.open('rb') as handle:
                entries = parse_feed(handle.read(_MAX_FEED_BYTES + 1))
        else:
            entries = fetch_items(args.url)
        print(json.dumps(summarize_entries(entries), ensure_ascii=False, indent=2))
    except (OSError, ValueError, HTTPError) as exc:
        parser.exit(2, f"stargaze-rss: {exc}\n")


if __name__ == "__main__":
    main()
