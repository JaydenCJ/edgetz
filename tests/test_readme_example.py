"""The README quickstart must actually run and print what the README shows.

The first ```python block in README.md is executed verbatim and its stdout is
compared against the ```text block that follows it, so the documentation can
never drift from reality.
"""

from __future__ import annotations

import io
import re
from contextlib import redirect_stdout
from pathlib import Path

README = Path(__file__).resolve().parent.parent / "README.md"
_FENCE = re.compile(r"```(\w+)\n(.*?)```", re.DOTALL)


def test_quickstart_snippet_produces_the_documented_output():
    blocks = _FENCE.findall(README.read_text(encoding="utf-8"))
    snippet = next(body for lang, body in blocks if lang == "python")
    index = next(i for i, (lang, _) in enumerate(blocks) if lang == "python")
    expected = next(body for lang, body in blocks[index:] if lang == "text")

    buffer = io.StringIO()
    with redirect_stdout(buffer):
        exec(compile(snippet, "README-quickstart", "exec"), {})  # noqa: S102
    assert buffer.getvalue().strip() == expected.strip()
