"""Tests for magnitude_setup (isolated experimental CLI)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

OPERATOR = Path(__file__).resolve().parents[1]
if str(OPERATOR) not in sys.path:
    sys.path.insert(0, str(OPERATOR))

from magnitude_setup.catalog import Preference, load_catalog, rank_models, score_model
from magnitude_setup.cli import main
from magnitude_setup.hardware import HardwareProfile, profile_hardware
from magnitude_setup.install import simulate_install, write_harness_config
from magnitude_setup.radar import render_radar


def test_profile_hardware_has_required_fields():
    hw = profile_hardware()
    assert hw.cores >= 1
    assert hw.memory_gb > 0
    assert hw.accel
    line = hw.summary_line()
    assert "cores" in line
    assert "GB" in line


def test_catalog_loads_and_ranks():
    hw = HardwareProfile(
        chip="Test CPU",
        os_label="Linux",
        arch="x86_64",
        cores=4,
        memory_gb=16.0,
        accel="CPU",
    )
    catalog = load_catalog()
    assert len(catalog) >= 8
    ranked = rank_models(hw, Preference.SMARTER, catalog=catalog, limit=10)
    assert len(ranked) == 10
    assert ranked[0].fit_score >= ranked[-1].fit_score
    # Smarter should prefer higher intelligence among fits
    smartest = rank_models(hw, Preference.SMARTEST, catalog=catalog, limit=3)
    fastest = rank_models(hw, Preference.FASTEST, catalog=catalog, limit=3)
    assert smartest[0].model.id != fastest[0].model.id or smartest[0].scores["intelligence"] >= fastest[0].scores["speed"]


def test_memory_fit_penalty():
    hw = HardwareProfile("CPU", "Linux", "x86_64", 4, 8.0, "CPU")
    catalog = load_catalog()
    heavy = next(m for m in catalog if m.memory_gb > 8)
    light = next(m for m in catalog if m.memory_gb < 5)
    heavy_score = score_model(heavy, hw, Preference.BALANCED)
    light_score = score_model(light, hw, Preference.BALANCED)
    assert light_score.fit_score > heavy_score.fit_score


def test_radar_render_five_axes():
    chart = render_radar([7.8, 9.1, 0.0, 7.4, 8.2], width=28, height=13)
    lines = chart.splitlines()
    assert len(lines) == 13
    assert any("●" in line or "◈" in line for line in lines)
    assert "INT" in chart or "SPD" in chart


def test_simulate_install_and_write_config(tmp_path: Path):
    hw = profile_hardware()
    ranked = rank_models(hw, Preference.SMARTER)[0]
    progress = list(simulate_install(ranked, demo=True, delay_s=0.0, steps=10))
    assert progress[-1][1] == 1.0
    path = write_harness_config(
        ranked=ranked,
        harness_id="concentric",
        preference="Smarter",
        hardware=hw.to_dict(),
        output_dir=tmp_path,
        demo=True,
    )
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["model"]["id"] == ranked.model.id
    assert data["harness"]["id"] == "concentric"
    assert data["concentric"]["enable_local"] is True
    assert (tmp_path / "local_model.env").exists()


def test_cli_profile_and_rank(capsys):
    assert main(["profile", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert "memory_gb" in payload

    assert main(["rank", "--preference", "Balanced", "--json", "--limit", "5"]) == 0
    ranked = json.loads(capsys.readouterr().out)
    assert len(ranked) == 5


def test_cli_setup_json(tmp_path: Path, capsys):
    out = tmp_path / "out"
    code = main(
        [
            "setup",
            "--json",
            "--demo",
            "--preference",
            "Smarter",
            "--harness",
            "concentric",
            "--output-dir",
            str(out),
            "--select",
            "1",
        ]
    )
    assert code == 0
    result = json.loads(capsys.readouterr().out)
    assert result["harness_id"] == "concentric"
    assert Path(result["config_path"]).exists()
    assert result["selected_model"]["model"]["name"]
