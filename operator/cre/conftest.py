"""Shared pytest fixtures for CRE integration tests.

Design rationale (evidence-based):

These fixtures solve a specific problem: test_drag_drop.py and
test_smooth_movement.py are *integration tests* that exercise real GUI
side effects via the CodexClient kernel (Hammerspoon HTTP server). They
were written as manual scripts with ``if __name__ == "__main__"`` blocks,
but their ``test_`` prefix causes pytest to collect them. When the kernel
isn't running, collection fails with "fixture 'client' not found."

Why conditional skip (not mocking, not renaming):

- **Meszaros (2007), xUnit Test Patterns, Ch. 16 — Slow Tests smell:**
  Integration tests that depend on external services should be *runnable
  when the service is available* and *gracefully skipped when it is not*.
  Permanently hiding them (rename) causes bit-rot; mocking pure side-effect
  calls (move_mouse, drag) tests nothing meaningful.

- **Humble Object pattern (Fowler, 2004; Meszaros, 2007):** These tests
  have no extractable logic to isolate — they ARE the side-effect layer.
  Mocking the side effects produces a test that asserts "I called mock.drag()"
  which validates nothing about the system.

- **pytest docs — "Skipping on a missing import dependency":** Module-level
  ``pytest.importorskip`` and session-scoped fixtures with ``pytest.skip()``
  are the recommended patterns for external-dependency gating.

- **IEEE 829 / SEI taxonomy:** These are *system integration tests*, not
  unit tests. Their natural run condition is "target system available."
  Conditional skip correctly classifies them: they appear as SKIPPED (not
  ERROR) in automated runs, and execute when the kernel is live.

References:
- Meszaros, G. (2007). xUnit Test Patterns: Refactoring Test Code. Addison-Wesley.
  Ch. 16 (Slow Tests), Ch. 23 (Test Double Patterns), Humble Object.
- Fowler, M. (2004). "Humble Object." martinfowler.com/bliki/HumbleObject.html
- pytest documentation: docs.pytest.org/how-to/skipping.html
  §"Skipping on a missing import dependency", §"Skip all test functions of
  a class or module" (pytestmark pattern).
- IEEE 829-2008, "Standard for Software and System Test Documentation."
- SEI/CMU, "A Taxonomy of Testing" (sei.cmu.edu/blog/a-taxonomy-of-testing).
"""

from __future__ import annotations

import pytest


def _kernel_available() -> bool:
    """Check if the CodexClient kernel (Hammerspoon) is reachable.

    Attempts a lightweight ping. Returns False on import failure,
    connection refusal, or timeout — any condition that means the
    kernel isn't running.
    """
    try:
        from codex_client import CodexClient
        client = CodexClient(timeout=1.0)
        result = client.ping()
        return isinstance(result, dict)
    except Exception:
        return False


_KERNEL_UP = _kernel_available()

_SKIP_REASON = (
    "CodexClient kernel (Hammerspoon) not available — "
    "these integration tests require a live kernel. "
    "Start the kernel and re-run to execute them."
)


# ---------------------------------------------------------------------------
# Fixtures for integration tests that need a live kernel
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def client():
    """Provide a live CodexClient, or skip the entire session's integration tests.

    Scope is session-level so we create one client and reuse it, matching
    the pattern in the ``if __main__`` blocks of the test scripts.
    """
    if not _KERNEL_UP:
        pytest.skip(_SKIP_REASON)
    from codex_client import CodexClient
    return CodexClient()


@pytest.fixture
def start_x() -> int:
    """Default drag start X (matches test_drag_drop.py __main__ block)."""
    return 100


@pytest.fixture
def start_y() -> int:
    """Default drag start Y."""
    return 100


@pytest.fixture
def end_x() -> int:
    """Default drag end X."""
    return 800


@pytest.fixture
def end_y() -> int:
    """Default drag end Y."""
    return 600


@pytest.fixture
def center_x() -> int:
    """Default circle/figure-eight center X."""
    return 720


@pytest.fixture
def center_y() -> int:
    """Default circle/figure-eight center Y."""
    return 450


@pytest.fixture
def radius() -> int:
    """Default radius for smooth-movement tests."""
    return 100
