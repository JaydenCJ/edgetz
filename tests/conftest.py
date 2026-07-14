"""Shared fixtures for the edgetz test suite.

Everything here is deterministic and offline: the corpus is static data, and
the only external input is the host tzdata, which ships with the OS/CI image
and does not change during a run.
"""

from __future__ import annotations

import pytest

import edgetz


@pytest.fixture(scope="session")
def corpus():
    """The full corpus, loaded once per session."""
    return edgetz.cases()


@pytest.fixture(scope="session")
def by_id(corpus):
    """Corpus indexed by case id."""
    return {item.id: item for item in corpus}
