"""Optional Phoenix/OpenTelemetry instrumentation for Concentric.

Designed to stay lightweight and safe when optional dependencies are absent.
The control room and other repo-local tools can import this module without
forcing Phoenix/OTel installation in the base runtime.
"""

from __future__ import annotations

import atexit
import os
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterator

try:
    from phoenix.otel import register as phoenix_register  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    phoenix_register = None

try:
    from opentelemetry import trace as otel_trace  # type: ignore
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter  # type: ignore
    from opentelemetry.sdk.resources import Resource  # type: ignore
    from opentelemetry.sdk.trace import TracerProvider  # type: ignore
    from opentelemetry.sdk.trace.export import BatchSpanProcessor  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    otel_trace = None
    OTLPSpanExporter = None
    Resource = None
    TracerProvider = None
    BatchSpanProcessor = None


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class ObservabilityStatus:
    available: bool
    enabled: bool
    service_name: str
    project_name: str
    collector_endpoint: str
    using_phoenix_otel: bool
    reason: str


class _NullSpan:
    def set_attribute(self, key: str, value: Any) -> None:
        return

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        return

    def record_exception(self, exc: BaseException) -> None:
        return


_STATUS = ObservabilityStatus(
    available=bool(
        (phoenix_register and otel_trace and Resource)
        or (otel_trace and OTLPSpanExporter and Resource and TracerProvider and BatchSpanProcessor)
    ),
    enabled=False,
    service_name="concentric",
    project_name=os.environ.get("PHOENIX_PROJECT_NAME", "concentric-study"),
    collector_endpoint=os.environ.get("PHOENIX_COLLECTOR_ENDPOINT", "http://127.0.0.1:6006/v1/traces"),
    using_phoenix_otel=False,
    reason="disabled",
)
_REGISTERED = False
_TRACER_PROVIDER = None


def ensure_observability(*, service_name: str, project_name: str | None = None) -> ObservabilityStatus:
    """Register Phoenix/OTel once when explicitly enabled via environment."""
    global _REGISTERED, _STATUS

    project = project_name or os.environ.get("PHOENIX_PROJECT_NAME", "concentric-study")
    collector = os.environ.get("PHOENIX_COLLECTOR_ENDPOINT", "http://127.0.0.1:6006/v1/traces")
    enabled = _truthy(os.environ.get("CONCENTRIC_OTEL_ENABLE"))

    if not enabled:
        _STATUS = ObservabilityStatus(
            available=bool(
                (phoenix_register and otel_trace and Resource)
                or (otel_trace and OTLPSpanExporter and Resource and TracerProvider and BatchSpanProcessor)
            ),
            enabled=False,
            service_name=service_name,
            project_name=project,
            collector_endpoint=collector,
            using_phoenix_otel=bool(phoenix_register),
            reason="CONCENTRIC_OTEL_ENABLE is not set",
        )
        return _STATUS

    if not (
        (phoenix_register and otel_trace and Resource)
        or (otel_trace and OTLPSpanExporter and Resource and TracerProvider and BatchSpanProcessor)
    ):
        _STATUS = ObservabilityStatus(
            available=False,
            enabled=False,
            service_name=service_name,
            project_name=project,
            collector_endpoint=collector,
            using_phoenix_otel=False,
            reason="Phoenix/OpenTelemetry dependencies are not installed",
        )
        return _STATUS

    os.environ.setdefault("PHOENIX_PROJECT_NAME", project)
    if not _REGISTERED:
        resource = Resource.create(
            {
                "service.name": service_name,
                "service.version": "0.1",
                "deployment.environment": "local",
                "concentric.project_name": project,
                "openinference.project.name": project,
            }
        )
        if phoenix_register:
            provider = phoenix_register(
                endpoint=collector,
                project_name=project,
                protocol="http/protobuf",
                batch=True,
                verbose=False,
                auto_instrument=False,
                resource=resource,
            )
        else:
            exporter = OTLPSpanExporter(endpoint=collector)
            provider = TracerProvider(resource=resource)
            provider.add_span_processor(BatchSpanProcessor(exporter))
            otel_trace.set_tracer_provider(provider)
        global _TRACER_PROVIDER
        _TRACER_PROVIDER = provider
        atexit.register(_shutdown_provider)
        _REGISTERED = True

    _STATUS = ObservabilityStatus(
        available=True,
        enabled=True,
        service_name=service_name,
        project_name=project,
        collector_endpoint=collector,
        using_phoenix_otel=bool(phoenix_register),
        reason="enabled",
    )
    return _STATUS


def _shutdown_provider() -> None:
    if _TRACER_PROVIDER is None:  # pragma: no cover - process shutdown path
        return
    try:
        _TRACER_PROVIDER.force_flush()
    except Exception:
        pass
    try:
        _TRACER_PROVIDER.shutdown()
    except Exception:
        pass


def get_status() -> ObservabilityStatus:
    return _STATUS


@contextmanager
def span(name: str, *, attributes: dict[str, Any] | None = None) -> Iterator[Any]:
    """Start an optional manual span; no-op when instrumentation is disabled."""
    status = _STATUS
    if not status.enabled or not otel_trace:
        yield _NullSpan()
        return

    tracer = otel_trace.get_tracer(status.service_name)
    with tracer.start_as_current_span(name) as current_span:
        for key, value in (attributes or {}).items():
            current_span.set_attribute(key, value)
        yield current_span


def status_payload() -> dict[str, Any]:
    status = get_status()
    return {
        "available": status.available,
        "enabled": status.enabled,
        "service_name": status.service_name,
        "project_name": status.project_name,
        "collector_endpoint": status.collector_endpoint,
        "using_phoenix_otel": status.using_phoenix_otel,
        "reason": status.reason,
    }
