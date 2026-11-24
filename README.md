# starGaze RSS

Turn overlapping news feeds into a concise brief with source links. starGaze RSS normalizes RSS, Atom, and structured JSON entries, groups similar headlines by token overlap, and extracts a summary from the source text.

## Try the offline fixture

From a checkout with Python 3.11 or newer:

```sh
python -m pip install .
stargaze-rss --file examples/synthetic.rss
```

The fictional harbor coverage becomes one brief item with two source links. An unrelated weather report remains a separate item. Output is JSON with `title`, `summary`, `published_at`, and `sources` fields.

## Work with your feeds

Use `--file` for a local feed or `--url` for an HTTP(S) feed you control. The standalone pipeline performs deduplication and summary extraction locally.

The [MIT-licensed release](LICENSE) preserves the 2025 legacy changes related to parsing, text cleaning, and headline similarity.
