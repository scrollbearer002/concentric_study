from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path


def _load_module():
    path = Path(__file__).resolve().parents[1] / "concentric_observability.py"
    spec = importlib.util.spec_from_file_location("concentric_observability_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["concentric_observability_test"] = module
    spec.loader.exec_module(module)
    return module


def test_status_payload_disabled_by_default(monkeypatch) -> None:
    monkeypatch.delenv("CONCENTRIC_OTEL_ENABLE", raising=False)
    monkeypatch.delenv("PHOENIX_PROJECT_NAME", raising=False)
    module = _load_module()

    status = module.ensure_observability(service_name="test-service", project_name="test-project")
    payload = module.status_payload()

    assert status.enabled is False
    assert payload["enabled"] is False
    assert payload["service_name"] == "test-service"
    assert payload["project_name"] == "test-project"


def test_span_context_manager_is_safe_when_disabled(monkeypatch) -> None:
    monkeypatch.setenv("CONCENTRIC_OTEL_ENABLE", "0")
    module = _load_module()

    with module.span("test.disabled.span") as current_span:
        current_span.set_attribute("concentric.test", "ok")
        current_span.add_event("noop")

    assert module.status_payload()["enabled"] is False
