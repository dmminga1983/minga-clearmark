# Contributing

Issues and PRs are welcome in English or Russian.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
ruff check .
```

- Keep `clearmark/locales/en.json` and `ru.json` in sync when you add a
  new user-facing CLI/server string — missing keys fall back to English
  automatically, so a partial PR is fine, but please don't leave `en.json`
  itself incomplete.
- New file-format support needs both an `inspect_*` and a `clean_*`
  function sharing one finding list (see `textclean.py` for the pattern),
  plus tests that assert a cleaned file re-inspects as not suspicious.
- No network calls from the core library — this project's whole point is
  running locally over content the user owns.
