# edgetz examples

Two runnable examples; both are exercised by the repository's own checks.

- **`test_safe_localize.py`** — a pytest module (collected by `pytest` from the
  repository root) showing the intended workflow: write a small, correct
  gap/fold-aware localizer, then let the edgetz corpus try to break it. Copy
  this shape into your own suite and point it at your scheduler, parser, or
  billing code instead.
- **`export_fixtures.py`** — a script for polyglot teams: exports the corpus
  as `cases.json`, `cases.jsonl`, and `cases.csv` so Go/Java/TypeScript test
  suites can consume the exact same fixtures. Run it with an output directory:

```bash
python examples/export_fixtures.py /tmp/fixtures
```

Both examples run fully offline against the corpus baked into the package.
