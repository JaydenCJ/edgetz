# Contributing to edgetz

Thanks for your interest in contributing. Issues, discussions, and pull
requests are all welcome — a new cursed datetime with a solid source is the
ideal first contribution.

## Development setup

```bash
git clone https://github.com/JaydenCJ/edgetz
cd edgetz
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Running the checks

```bash
pytest                 # unit tests + example tests (tests/ and examples/)
bash scripts/smoke.sh  # end-to-end CLI smoke: browse, export, verify
```

Both must pass before a pull request is reviewed; `scripts/smoke.sh` drives
the real CLI end to end and must print `SMOKE OK`. Everything runs fully
offline — the only external input is the host's own tzdata.

## Adding a case to the corpus

1. Pick a **real** event: a tzdata transition, an IERS bulletin, a calendar
   rule. Synthetic or hypothetical datetimes are out of scope.
2. Add the `Case` to `src/edgetz/corpus.py` in its category block, with a
   `why` that names the bug class it triggers and a `source` with provenance.
3. Fill `expect` with machine-checkable ground truth and set `verify` to
   `tzdata` or `calendar` whenever possible; `none` needs justification.
4. Run `edgetz verify` — your new case must come back `ok` (or `skipped`
   with reason), and the whole suite must stay green.

## Ground rules

- **No new runtime dependencies.** The package is standard-library only;
  that is a feature. Test-only dependencies belong in the `dev` extra.
- **Never guess ground truth.** Every offset and instant in the corpus must
  be reproducible from the named source; `edgetz verify` is the referee.
- **Every public API needs an English docstring and a test.** The README
  quickstart is executed verbatim by `tests/test_readme_example.py`, so keep
  code and docs in sync.
- **Keep the three READMEs aligned.** `README.md`, `README.zh.md`, and
  `README.ja.md` are line-for-line parallel; update all three when you
  change one (English is the authoritative version).

## Reporting bugs

Please include `edgetz --version` output, your host tzdata version (the
first line `edgetz verify` prints), and the case id involved. For corpus
disputes, cite the tzdata region file or bulletin you believe is correct.

## Security

Please do not open public issues for security problems; use GitHub's private
vulnerability reporting on this repository instead.
