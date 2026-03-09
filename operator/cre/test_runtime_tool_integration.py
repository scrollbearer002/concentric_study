from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from agent import _run_benchmark_evaluation, _stop_visual_monitor
import agent_infra.recovery as recovery


class _FakeSnapshot:
    def __init__(self, path: str, index: int) -> None:
        self._path = path
        self._index = index

    def to_dict(self) -> dict:
        return {
            "path": self._path,
            "timestamp": 0.0,
            "iso_time": "2026-02-28T00:00:00Z",
            "index": self._index,
        }


class _FakeMonitor:
    def __init__(self, output_dir: Path) -> None:
        self._output_dir = output_dir
        self._snapshots = [
            _FakeSnapshot(str(output_dir / "snap_0000.png"), 0),
            _FakeSnapshot(str(output_dir / "snap_0001.png"), 1),
        ]
        self.stopped = False

    @property
    def snapshot_count(self) -> int:
        return len(self._snapshots)

    def stop(self) -> None:
        self.stopped = True

    def timeline(self, last_n: int = 10):
        return self._snapshots[-last_n:]

    def get_status(self) -> dict:
        latest = self._snapshots[-1]
        return {
            "running": False,
            "total_captures": len(self._snapshots),
            "buffer_size": len(self._snapshots),
            "interval_seconds": 5.0,
            "latest_path": latest.to_dict()["path"],
            "latest_time": latest.to_dict()["iso_time"],
        }


class _FakeTraceWriter:
    def __init__(self, run_dir: Path) -> None:
        self.run_dir = run_dir
        self.manifest_path = run_dir / "manifest.json"


def test_stop_visual_monitor_persists_status_and_timeline(tmp_path: Path):
    run_dir = tmp_path / "runs" / "abc123"
    run_dir.mkdir(parents=True)
    monitor_dir = run_dir / "visual_monitor"
    monitor_dir.mkdir()
    monitor = _FakeMonitor(monitor_dir)
    trace_writer = _FakeTraceWriter(run_dir)

    checkpoints = [{"phase": "after_recovery_action", "path": "snap.png"}]
    artifact = _stop_visual_monitor(monitor, trace_writer, checkpoints=checkpoints)

    assert monitor.stopped is True
    assert artifact is not None
    assert (monitor_dir / "status.json").exists()
    assert (monitor_dir / "timeline.json").exists()
    assert (monitor_dir / "checkpoints.json").exists()

    status = json.loads((monitor_dir / "status.json").read_text(encoding="utf-8"))
    timeline = json.loads((monitor_dir / "timeline.json").read_text(encoding="utf-8"))
    persisted_checkpoints = json.loads((monitor_dir / "checkpoints.json").read_text(encoding="utf-8"))
    assert status["total_captures"] == 2
    assert len(timeline) == 2
    assert persisted_checkpoints == checkpoints


def test_run_benchmark_evaluation_uses_default_claims_and_saves_result(tmp_path: Path):
    run_dir = tmp_path / "runs" / "bench001"
    run_dir.mkdir(parents=True)

    manifest = {
        "run_id": "bench001",
        "task_id": "OPEN_PAGE",
        "task_description": "Open the requested page",
        "outcome": "success",
        "total_duration_ms": 42000,
        "agent_config": {"url": "https://example.com"},
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    trace_lines = [
        {
            "step": 1,
            "action": {"type": "kleki_set_color", "parameters": {}},
            "action_result": {"success": True},
        },
        {
            "step": 997,
            "action": {"type": "final_verification_gate", "parameters": {}},
            "action_result": {"success": True},
        },
    ]
    with open(run_dir / "trace.jsonl", "w", encoding="utf-8") as f:
        for line in trace_lines:
            f.write(json.dumps(line) + "\n")

    trace_writer = _FakeTraceWriter(run_dir)
    payload = _run_benchmark_evaluation(trace_writer, plan=[{"action": "kleki_set_color"}])

    assert payload is not None
    assert payload["claims_total"] == 4
    assert payload["claims_satisfied"] == 4
    assert payload["claims_score"] == 1.0
    assert (run_dir / "benchmark_result.json").exists()


def test_run_benchmark_evaluation_prefers_normalized_task_result(tmp_path: Path):
    run_dir = tmp_path / "runs" / "bench002"
    run_dir.mkdir(parents=True)

    manifest = {
        "run_id": "bench002",
        "task_id": "OPEN_PAGE",
        "task_description": "Open the requested page",
        "outcome": "success",
        "outcome_semantics": {
            "task_result": "accepted",
            "execution_result": "success",
            "final_verification": {"status": "not_run"},
        },
        "total_duration_ms": 42000,
        "agent_config": {"url": "https://example.com"},
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    trace_lines = [
        {
            "step": 1,
            "action": {"type": "click", "parameters": {}},
            "action_result": {"success": True},
        },
    ]
    with open(run_dir / "trace.jsonl", "w", encoding="utf-8") as f:
        for line in trace_lines:
            f.write(json.dumps(line) + "\n")

    trace_writer = _FakeTraceWriter(run_dir)
    payload = _run_benchmark_evaluation(trace_writer, plan=[{"action": "click"}])

    assert payload is not None
    detail = {item["description"]: item for item in payload["claims_detail"]}
    assert detail["Run outcome is success"]["satisfied"] is True


def test_run_benchmark_evaluation_adds_art_specific_claims(tmp_path: Path):
    run_dir = tmp_path / "runs" / "art001"
    run_dir.mkdir(parents=True)

    manifest = {
        "run_id": "art001",
        "task_id": "DRAW_SKYSCRAPER",
        "task_description": "Draw a tall skyscraper with grayscale shading",
        "outcome": "failure",
        "total_duration_ms": 84000,
        "agent_config": {"url": "https://kleki.com"},
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    trace_lines = [
        {
            "step": 1,
            "action": {"type": "kleki_set_color", "parameters": {}},
            "action_result": {"success": True},
        },
        {
            "step": 2,
            "action": {"type": "kleki_set_brush_size", "parameters": {}},
            "action_result": {"success": True},
        },
        {
            "step": 3,
            "action": {"type": "draw_path", "parameters": {}},
            "action_result": {"success": True},
        },
        {
            "step": 4,
            "action": {"type": "draw_path", "parameters": {}},
            "action_result": {"success": True},
        },
        {
            "step": 5,
            "action": {"type": "draw_path", "parameters": {}},
            "action_result": {"success": True},
        },
        {
            "step": 997,
            "action": {"type": "final_verification_gate", "parameters": {}},
            "action_result": {"success": False},
            "post_state": {
                "constraints": [
                    {"description": "Canvas is not empty — visible drawing/content present", "category": "existence", "satisfied": True},
                    {"description": "Drawing fills a substantial portion of the canvas (>30%)", "category": "composition", "satisfied": True},
                    {"description": "A recognizable tall skyscraper or high-rise building is clearly present", "category": "subject", "satisfied": True},
                    {"description": "Visible shading or tonal modeling is present, not just outline strokes", "category": "subject", "satisfied": False},
                ]
            },
        },
    ]
    with open(run_dir / "trace.jsonl", "w", encoding="utf-8") as f:
        for line in trace_lines:
            f.write(json.dumps(line) + "\n")

    trace_writer = _FakeTraceWriter(run_dir)
    payload = _run_benchmark_evaluation(
        trace_writer,
        plan=[
            {"action": "kleki_set_color"},
            {"action": "kleki_set_brush_size"},
            {"action": "draw_path"},
            {"action": "draw_path"},
            {"action": "draw_path"},
        ],
    )

    assert payload is not None
    assert payload["claims_total"] == 13
    detail = {item["description"]: item for item in payload["claims_detail"]}
    assert detail["Art task reached active drawing phase"]["satisfied"] is True
    assert detail["Art task exercised rendering controls relevant to style"]["satisfied"] is True
    assert detail["Art verification shows meaningful visual progress"]["satisfied"] is True
    assert detail["Art output is a recognizable subject"]["satisfied"] is True
    assert detail["Art output maintains perspective coherence"]["satisfied"] is False


def test_capture_visual_monitor_checkpoint_records_phase():
    class FakeMonitor:
        def capture_now(self):
            return SimpleNamespace(
                path="/tmp/snap.png",
                timestamp=123.0,
                iso_time="2026-02-28T00:00:00Z",
                index=7,
            )

    recovery._exec_log_line = lambda *args, **kwargs: None
    ctx = SimpleNamespace(
        visual_monitor=FakeMonitor(),
        visual_monitor_checkpoints=[],
    )

    checkpoint = recovery._capture_visual_monitor_checkpoint(
        ctx,
        "after_recovery_action",
        step_index=4,
        attempt=1,
        action_type="escape",
        diagnosis={"recovery_action": "escape", "obstruction": True, "description": "Leave-page dialog"},
    )

    assert checkpoint is not None
    assert checkpoint["phase"] == "after_recovery_action"
    assert checkpoint["step"] == 4
    assert checkpoint["attempt"] == 1
    assert checkpoint["action_type"] == "escape"
    assert checkpoint["recovery_action"] == "escape"
    assert len(ctx.visual_monitor_checkpoints) == 1
