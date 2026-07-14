"""Exception hierarchy for edgetz.

Everything raised on purpose by this package derives from :class:`EdgetzError`,
so callers can catch one type at the boundary. Unknown-identifier errors carry
the offending value and, where possible, close-match suggestions.
"""

from __future__ import annotations


class EdgetzError(Exception):
    """Base class for all errors raised by edgetz."""


class UnknownCaseError(EdgetzError):
    """Raised when a case id does not exist in the corpus."""

    def __init__(self, case_id: str, suggestions: tuple = ()):
        self.case_id = case_id
        self.suggestions = tuple(suggestions)
        msg = f"unknown case id: {case_id!r}"
        if self.suggestions:
            msg += " (did you mean: " + ", ".join(self.suggestions) + "?)"
        super().__init__(msg)


class UnknownFilterError(EdgetzError):
    """Raised when a filter value (category, zone, tag, kind) is not in the corpus."""

    def __init__(self, field: str, value: str, allowed: tuple = ()):
        self.field = field
        self.value = value
        self.allowed = tuple(allowed)
        msg = f"unknown {field}: {value!r}"
        if self.allowed:
            msg += " (known: " + ", ".join(self.allowed) + ")"
        super().__init__(msg)
