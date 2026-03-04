from __future__ import annotations

import json
from pathlib import Path

from agent import (
    CheckpointResult,
    ExecutionCheckpoint,
    ExecutionContext,
    _build_execution_checkpoints,
    _persist_execution_checkpoints,
    _run_execution_checkpoint,
)
from agent_infra.research_agent import EquationSolution, MethodBrief, MethodStep, ResearchBrief


class _FakeTraceWriter:
    def __init__(self, run_dir: Path) -> None:
        self.run_dir = str(run_dir)


class _FakeAgent:
    def __init__(self, failures_before_success: int = 0) -> None:
        self.failures_before_success = failures_before_success
        self.assert_calls = 0
        self.focus_calls = 0

    def assert_visual_state(self, screenshot_path: str, assertion: str) -> None:
        self.assert_calls += 1
        if self.assert_calls <= self.failures_before_success:
            raise RuntimeError(f"assert failed: {assertion}")

    def enforce_app_focus(self, app_name: str) -> None:
        self.focus_calls += 1


class _FakeMonitor:
    def __init__(self) -> None:
        self.captures = 0

    def capture_now(self):
        self.captures += 1

        class _Snap:
            def __init__(self, idx: int) -> None:
                self.path = f"/tmp/fake_monitor_{idx}.png"

        return _Snap(self.captures)


def _write_png(path: Path) -> None:
    from PIL import Image

    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (10, 10), "white").save(path)


def _ctx(tmp_path: Path, agent: _FakeAgent | None = None) -> ExecutionContext:
    ctx = ExecutionContext(
        use_enterprise=True,
        agent=agent,
        vision_engine=None,
        ui_analysis={},
        cre_dir=tmp_path,
        current_state_path=str(tmp_path / "state.png"),
        trace_writer=_FakeTraceWriter(tmp_path / "run"),
        capabilities=None,
        action_space=None,
        url="https://example.com",
        goal="Complete a mixed workflow.",
    )
    ctx.visual_monitor = _FakeMonitor()
    return ctx


def test_build_execution_checkpoints_from_equation_plan() -> None:
    brief = ResearchBrief(
        task_description="Do the task",
        method_brief=MethodBrief(
            subject_family="general",
            task_family="mixed",
            steps=[
                MethodStep(step_id="step_01", description="Open target"),
                MethodStep(step_id="step_02", description="Confirm result"),
            ],
        ),
        equation_solution=EquationSolution(
            execution_plan=[
                {
                    "step_index": 1,
                    "step_id": "step_01",
                    "description": "Open the target page.",
                    "verification_hint": "The target page is visible.",
                    "is_major": True,
                },
                {
                    "step_index": 2,
                    "step_id": "step_02",
                    "description": "Confirm the page result.",
                    "verification_hint": "The expected result is visible.",
                    "is_major": True,
                },
            ]
        ),
    )
    ctx = _ctx(Path("/tmp/phase4_build_checkpoints"))
    ctx.research_brief = brief

    checkpoints = _build_execution_checkpoints(
        ctx,
        [
            {"action": "click", "description": "Open target"},
            {"action": "visual_assert", "args": {"assertion": "The expected result is visible."}},
        ],
    )

    assert [checkpoint.trigger_step_index for checkpoint in checkpoints] == [1, 2]
    assert checkpoints[0].description == "The target page is visible."
    assert checkpoints[0].comparison_mode == "reference-free"
    assert checkpoints[0].method_step_id == "step_01"


def test_run_execution_checkpoint_refines_after_first_failure(monkeypatch, tmp_path: Path) -> None:
    agent = _FakeAgent(failures_before_success=1)
    ctx = _ctx(tmp_path, agent=agent)

    def fake_capture(path, *args, **kwargs):
        _write_png(Path(path))

    monkeypatch.setattr("agent.capture_front_window", fake_capture)

    checkpoint = ExecutionCheckpoint(
        checkpoint_id="step_001",
        trigger_step_index=1,
        description="The expected panel is visible.",
        comparison_mode="reference-free",
        refinement_required_on_fail=True,
        assertion="The expected panel is visible.",
    )

    result = _run_execution_checkpoint(ctx, checkpoint)

    assert result.passed is True
    assert result.next_action == "refined_and_continue"
    assert result.iteration == 2
    assert agent.assert_calls == 2
    assert agent.focus_calls == 1
    assert len(ctx.visual_monitor_checkpoints) == 2



def test_persist_execution_checkpoints_writes_run_artifact(tmp_path: Path) -> None:
    ctx = _ctx(tmp_path, agent=_FakeAgent())
    ctx.execution_checkpoints = [
        CheckpointResult(
            checkpoint_id="step_001",
            current_image="/tmp/checkpoint.png",
            comparison_result={"mode": "reference-free", "result": "passed"},
            passed=True,
            deficiencies=[],
            next_action="continue",
            trigger_step_index=1,
            comparison_mode="reference-free",
        ).to_dict()
    ]

    _persist_execution_checkpoints(ctx)

    path = Path(ctx.trace_writer.run_dir) / "execution_checkpoints.json"
    assert path.exists()
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload[0]["checkpoint_id"] == "step_001"


def test_reference_free_checkpoint_records_iteration_on_first_pass(monkeypatch, tmp_path: Path) -> None:
    agent = _FakeAgent(failures_before_success=0)
    ctx = _ctx(tmp_path, agent=agent)

    def fake_capture(path, *args, **kwargs):
        _write_png(Path(path))

    monkeypatch.setattr("agent.capture_front_window", fake_capture)

    checkpoint = ExecutionCheckpoint(
        checkpoint_id="step_002",
        trigger_step_index=2,
        description="The expected result is visible.",
        comparison_mode="reference-free",
        refinement_required_on_fail=True,
        assertion="The expected result is visible.",
    )

    result = _run_execution_checkpoint(ctx, checkpoint)

    assert result.passed is True
    assert result.iteration == 1
    assert result.next_action == "continue"
