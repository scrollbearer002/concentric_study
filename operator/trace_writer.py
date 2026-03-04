"""Backward-compatible shim — canonical source is agent_infra.trace_writer."""
from agent_infra.trace_writer import *  # noqa: F401,F403
from agent_infra.trace_writer import TraceWriter, TraceStep, _iso_now, _iso_to_epoch, _get_platform_info
