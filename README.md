# starGaze RSS

A small standalone news pipeline derived from the 2025 starGaze legacy collector and rolling deduplication code. It normalizes feed entries, groups near-duplicate headlines by token overlap, and emits an extractive brief with source links.

```sh
python -m pip install .
stargaze-rss --file examples/synthetic.rss
```

To read a feed you control, pass its HTTP(S) URL with `--url`. The offline example uses fictional inputs. The extraction preserves the relevant historical changes to parsing, cleaning, and similarity. The standalone CLI uses headline similarity and source text in place of the original services for embeddings, persistent storage, and model-generated summaries.
