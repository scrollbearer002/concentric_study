"""Host-tool health discovery and backend selection for the live repo environment.

This layer models the local machine substrate explicitly before capability
activation begins. It is intentionally below planning/site learning and above
the raw OS substrate: diagnostic and gating, not behavior-shaping.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


OPERATOR_DIR = Path(__file__).resolve().parents[1]
ROOT = OPERATOR_DIR.parent
DEFAULT_CATALOG_PATH = Path(__file__).with_name("tool_health_catalog.json")


@dataclass
class CheckResult:
    name: str
    check_type: str
    passed: bool
    detail: str
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None


def required_classes_for_task(reqs: Any | None = None, *, has_url: bool = False) -> list[str]:
    required = [
        "runtime_python_selected",
        "macos_ui_automation",
        "native_event_backend",
        "screen_capture",
    ]
    needs_browser = has_url
    if reqs is not None:
        needs_browser = needs_browser or any(
            getattr(reqs, attr, False)
            for attr in ("needs_navigation", "needs_drawing", "needs_form_fill", "needs_login")
        )
    if needs_browser:
        required.append("browser_target")
    return required


class HostToolHealth:
    def __init__(
        self,
        *,
        operator_dir: str | Path | None = None,
        cre_dir: str | Path | None = None,
        catalog_path: str | Path | None = None,
    ) -> None:
        self.operator_dir = Path(operator_dir) if operator_dir else OPERATOR_DIR
        self.root = self.operator_dir.parent
        self.cre_dir = Path(cre_dir) if cre_dir else self.operator_dir / "cre"
        self.catalog_path = Path(catalog_path) if catalog_path else DEFAULT_CATALOG_PATH
        self.catalog = json.loads(self.catalog_path.read_text(encoding="utf-8"))

    def evaluate(self, reqs: Any | None = None, *, has_url: bool = False) -> dict[str, Any]:
        tools_cfg = self.catalog.get("tools", {})
        classes_cfg = self.catalog.get("tool_classes", {})
        required_classes = required_classes_for_task(reqs, has_url=has_url)

        tools_status: dict[str, Any] = {}
        for tool_id, spec in sorted(tools_cfg.items()):
            checks = []
            available = True
            for check in spec.get("checks", []):
                result = self._run_check(check)
                checks.append(asdict(result))
                available = available and result.passed
            tools_status[tool_id] = {
                "description": spec.get("description", ""),
                "provides": list(spec.get("provides", [])),
                "available": available,
                "checks": checks,
            }

        class_rows: dict[str, Any] = {}
        selected: dict[str, str] = {}
        missing_required: list[str] = []

        for class_id, spec in sorted(classes_cfg.items()):
            prefer = [str(item) for item in spec.get("prefer", [])]
            providers = sorted(
                tool_id
                for tool_id, status in tools_status.items()
                if class_id in status.get("provides", []) and status.get("available")
            )
            chosen = ""
            for tool_id in prefer:
                if tool_id in providers:
                    chosen = tool_id
                    break
            if not chosen and providers:
                chosen = providers[0]
            if chosen:
                selected[class_id] = chosen
            required = class_id in required_classes
            if required and not chosen:
                missing_required.append(class_id)
            class_rows[class_id] = {
                "required": required,
                "preferred_order": prefer,
                "available_providers": providers,
                "selected_tool": chosen or None,
            }

        payload = {
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "catalog_path": str(self.catalog_path.relative_to(self.root)),
            "catalog_version": self.catalog.get("version"),
            "environment": {
                "repo_root": str(self.root),
                "operator_dir": str(self.operator_dir),
                "cre_dir": str(self.cre_dir),
                "operator_python": str(self.operator_python),
                "python_executable": sys.executable,
                "platform": sys.platform,
            },
            "required_classes": required_classes,
            "tools": tools_status,
            "classes": class_rows,
            "selected": selected,
            "missing_required_classes": missing_required,
            "all_required_ready": not missing_required,
        }
        return payload

    def summary(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "catalog_version": payload.get("catalog_version"),
            "required_classes": payload.get("required_classes"),
            "selected": payload.get("selected"),
            "missing_required_classes": payload.get("missing_required_classes"),
            "all_required_ready": payload.get("all_required_ready"),
        }

    @property
    def operator_python(self) -> Path:
        return self.operator_dir / "venv" / "bin" / "python"

    def _resolve(self, value: str) -> str:
        replacements = {
            "{{repo_root}}": str(self.root),
            "{{operator_dir}}": str(self.operator_dir),
            "{{cre_dir}}": str(self.cre_dir),
            "{{operator_python}}": str(self.operator_python),
            "{{safari_app}}": "/Applications/Safari.app",
        }
        resolved = value
        for token, replacement in replacements.items():
            resolved = resolved.replace(token, replacement)
        return resolved

    def _run_check(self, check: dict[str, Any]) -> CheckResult:
        name = str(check.get("name", "unnamed_check"))
        check_type = str(check.get("type", ""))
        if check_type == "command_exists":
            command = self._resolve(str(check["command"]))
            found = shutil.which(command) is not None
            return CheckResult(name=name, check_type=check_type, passed=found, detail=command if found else f"missing:{command}")

        if check_type == "file_exists":
            path = Path(self._resolve(str(check["path"])))
            exists = path.exists()
            return CheckResult(name=name, check_type=check_type, passed=exists, detail=str(path))

        if check_type == "command":
            argv = [self._resolve(str(part)) for part in check.get("argv", [])]
            return self._run_subprocess_check(name=name, check_type=check_type, argv=argv, expect_regex=check.get("expect_regex"))

        if check_type == "python_imports":
            executable = self._resolve(str(check["executable"]))
            modules = [str(module) for module in check.get("modules", [])]
            code = "\n".join([f"import {module}" for module in modules]) + "\nprint('ok')"
            return self._run_subprocess_check(
                name=name,
                check_type=check_type,
                argv=[executable, "-c", code],
                expect_regex=r"^ok\s*$",
            )

        if check_type == "python_code":
            executable = self._resolve(str(check["executable"]))
            code = str(check["code"])
            return self._run_subprocess_check(
                name=name,
                check_type=check_type,
                argv=[executable, "-c", code],
                expect_regex=check.get("expect_regex"),
            )

        raise ValueError(f"Unsupported check type: {check_type}")

    def _run_subprocess_check(
        self,
        *,
        name: str,
        check_type: str,
        argv: list[str],
        expect_regex: str | None,
    ) -> CheckResult:
        try:
            proc = subprocess.run(
                argv,
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=5,
            )
        except Exception as exc:  # pragma: no cover - exceptional path
            return CheckResult(
                name=name,
                check_type=check_type,
                passed=False,
                detail="exception",
                stderr=str(exc),
            )
        stdout = (proc.stdout or "").strip()
        stderr = (proc.stderr or "").strip()
        passed = proc.returncode == 0
        if passed and expect_regex:
            target = stdout if stdout else stderr
            passed = bool(re.search(str(expect_regex), target, flags=re.MULTILINE))
        return CheckResult(
            name=name,
            check_type=check_type,
            passed=passed,
            detail=" ".join(argv),
            stdout=stdout[:500],
            stderr=stderr[:500],
            exit_code=proc.returncode,
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate host-tool health for the live concentric_study environment.")
    parser.add_argument("--json", action="store_true", help="Print full JSON payload.")
    parser.add_argument("--summary", action="store_true", help="Print the reduced summary payload.")
    parser.add_argument("--has-url", action="store_true", help="Include browser_target in required classes.")
    args = parser.parse_args(argv)

    checker = HostToolHealth()
    payload = checker.evaluate(has_url=args.has_url)
    if args.summary or not args.json:
        print(json.dumps(checker.summary(payload), indent=2, sort_keys=False))
    else:
        print(json.dumps(payload, indent=2, sort_keys=False))
    return 0 if payload["all_required_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
