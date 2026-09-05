"""Textual TUI for magnitude setup — choose → install → harness."""

from __future__ import annotations

from pathlib import Path

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Footer, Label, ListItem, ListView, ProgressBar, Static

from ..catalog import Preference, RankedModel, rank_models
from ..hardware import HardwareProfile, profile_hardware
from ..install import HARNESSES, simulate_install, write_harness_config
from ..radar import metric_lines, render_radar


class Stepper(Static):
    step: reactive[int] = reactive(0)

    def render(self) -> str:
        labels = ["Choose model", "Install model", "Select harness"]
        parts = []
        for i, label in enumerate(labels):
            mark = "●" if i <= self.step else "○"
            style_open = "" if i > self.step else ""
            parts.append(f"{mark} {label}")
        return "  ——  ".join(parts)


class PreferenceBar(Static):
    preference: reactive[Preference] = reactive(Preference.SMARTER)

    def render(self) -> str:
        chunks = []
        for p in Preference.ordered():
            if p is self.preference:
                chunks.append(f"[bold reverse] {p.value} [/]")
            else:
                chunks.append(f"[dim]{p.value}[/]")
        return " — ".join(chunks)


class RadarPane(Static):
    def show_model(self, ranked: RankedModel) -> None:
        radar = render_radar(
            [
                ranked.scores["intelligence"],
                ranked.scores["speed"],
                ranked.scores["speculation"],
                ranked.scores["memory"],
                ranked.scores["accuracy"],
            ],
            width=30,
            height=14,
        )
        meta = (
            f"[bold]{ranked.model.display_name}[/]\n"
            f"[dim]{ranked.model.context_k}K CONTEXT · {ranked.model.days_ago} days ago · "
            f"{ranked.model.architecture} · {ranked.model.modalities}[/]\n\n"
            f"[cyan]{radar}[/]\n\n"
            + "\n".join(metric_lines(ranked))
        )
        self.update(meta)


class MagnitudeSetupApp(App[dict]):
    """Interactive setup matching the reference TUI screenshots."""

    CSS = """
    Screen {
        background: #0a0a0a;
        color: #e8e8e8;
    }
    #header {
        dock: top;
        height: 7;
        padding: 1 2;
        border-bottom: solid #1e4fd6;
    }
    #title {
        text-style: bold;
        color: #ffffff;
    }
    #hw {
        color: #6cb6ff;
    }
    #progress-wrap {
        height: 3;
        padding: 0 2;
    }
    #main {
        height: 1fr;
        padding: 0 1;
    }
    #left {
        width: 1fr;
        padding: 1;
    }
    #right {
        width: 1fr;
        padding: 1;
        border-left: solid #222;
    }
    #section {
        text-style: bold;
        color: #888;
        margin-bottom: 1;
    }
    ListView {
        height: auto;
        max-height: 16;
    }
    ListItem {
        padding: 0 1;
    }
    .selected-hint {
        color: #6cb6ff;
        text-style: bold;
    }
    #radar {
        height: auto;
    }
    Footer {
        background: #111;
    }
    """

    BINDINGS = [
        Binding("left", "pref_left", "Slower/faster", show=True),
        Binding("right", "pref_right", "Smarter", show=True),
        Binding("enter", "confirm", "Download / Select", show=True),
        Binding("escape", "cancel", "Cancel", show=True),
    ]

    preference: reactive[Preference] = reactive(Preference.SMARTER)
    step: reactive[int] = reactive(0)

    def __init__(
        self,
        *,
        demo: bool = True,
        output_dir: Path | None = None,
        initial_preference: Preference = Preference.SMARTER,
    ) -> None:
        super().__init__()
        self.demo = demo
        self.output_dir = output_dir or Path("operator/cre/runs/magnitude_setup_demo")
        self.preference = initial_preference
        self.hw: HardwareProfile = profile_hardware()
        self.ranked: list[RankedModel] = []
        self.selected_index = 0
        self.chosen: RankedModel | None = None
        self.harness_index = 0
        self.result: dict | None = None
        self._installing = False

    def compose(self) -> ComposeResult:
        with Vertical(id="header"):
            yield Label("MAGNITUDE SETUP", id="title")
            yield Stepper(id="stepper")
            yield Label(self.hw.summary_line(), id="hw")
            yield PreferenceBar(id="pref")
        with Vertical(id="progress-wrap"):
            yield Label("", id="progress-label")
            yield ProgressBar(total=100, show_eta=False, id="progress")
        with Horizontal(id="main"):
            with Vertical(id="left"):
                yield Label("RECOMMENDED MODELS", id="section")
                yield ListView(id="models")
                yield Label("ON THIS COMPUTER", id="local-label")
                yield ListView(id="local-models")
            with Vertical(id="right"):
                yield RadarPane(id="radar")
                yield ListView(id="harnesses")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#harnesses", ListView).display = False
        self.query_one("#progress", ProgressBar).update(progress=0)
        self.refresh_models()
        self.query_one("#models", ListView).focus()

    def watch_preference(self, pref: Preference) -> None:
        bar = self.query_one("#pref", PreferenceBar)
        bar.preference = pref
        if self.step == 0:
            self.refresh_models()

    def watch_step(self, step: int) -> None:
        self.query_one("#stepper", Stepper).step = step
        pref = self.query_one("#pref", PreferenceBar)
        pref.display = step == 0
        self.query_one("#models", ListView).display = step == 0
        self.query_one("#local-models", ListView).display = step == 0
        self.query_one("#local-label", Label).display = step == 0
        self.query_one("#section", Label).display = step == 0
        self.query_one("#radar", RadarPane).display = step in {0, 1}
        self.query_one("#harnesses", ListView).display = step == 2
        if step == 2:
            self.populate_harnesses()
            self.query_one("#harnesses", ListView).focus()

    def refresh_models(self) -> None:
        self.ranked = rank_models(self.hw, self.preference)
        self.selected_index = min(self.selected_index, max(0, len(self.ranked) - 1))
        models = self.query_one("#models", ListView)
        models.clear()
        for i, r in enumerate(self.ranked):
            tag = "  Load" if r.model.loadable else ""
            label = f"{i + 1}. {r.model.display_name}{tag}"
            models.append(ListItem(Label(label)))
        local = self.query_one("#local-models", ListView)
        local.clear()
        for r in self.ranked:
            if r.model.installed:
                local.append(ListItem(Label(f"{r.model.name}  Load")))
        if self.ranked:
            self._show_selected()

    def _show_selected(self) -> None:
        if not self.ranked:
            return
        ranked = self.ranked[self.selected_index]
        self.query_one("#radar", RadarPane).show_model(ranked)

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if event.list_view.id == "models" and event.list_item is not None:
            idx = event.list_view.index or 0
            self.selected_index = idx
            self._show_selected()
        elif event.list_view.id == "harnesses" and event.list_item is not None:
            self.harness_index = event.list_view.index or 0

    def action_pref_left(self) -> None:
        if self.step != 0:
            return
        ordered = Preference.ordered()
        i = max(0, self.preference.index() - 1)
        self.preference = ordered[i]

    def action_pref_right(self) -> None:
        if self.step != 0:
            return
        ordered = Preference.ordered()
        i = min(len(ordered) - 1, self.preference.index() + 1)
        self.preference = ordered[i]

    def action_cancel(self) -> None:
        self.exit({"cancelled": True})

    def action_confirm(self) -> None:
        if self._installing:
            return
        if self.step == 0:
            if not self.ranked:
                return
            self.chosen = self.ranked[self.selected_index]
            self.step = 1
            self.run_install()
        elif self.step == 2:
            self.finish()

    @work(exclusive=True)
    async def run_install(self) -> None:
        from asyncio import sleep

        assert self.chosen is not None
        self._installing = True
        label = self.query_one("#progress-label", Label)
        bar = self.query_one("#progress", ProgressBar)
        for status, pct in simulate_install(self.chosen, demo=self.demo, delay_s=0.0):
            label.update(status)
            bar.update(progress=pct * 100)
            self.query_one("#radar", RadarPane).show_model(self.chosen)
            await sleep(0.025)
        self._installing = False
        label.update(f"Installed {self.chosen.model.display_name}")
        self.step = 2

    def populate_harnesses(self) -> None:
        view = self.query_one("#harnesses", ListView)
        view.clear()
        for h in HARNESSES:
            view.append(ListItem(Label(f"{h['name']} — {h['blurb']}")))
        self.query_one("#section", Label).update("SELECT HARNESS")
        # section may be hidden; show a note on radar pane
        self.query_one("#radar", RadarPane).update(
            f"[bold]Selected model[/]\n{self.chosen.model.display_name if self.chosen else ''}\n\n"
            "[dim]Enter to write harness config · Esc to cancel[/]"
        )

    def finish(self) -> None:
        assert self.chosen is not None
        harness = HARNESSES[self.harness_index]
        path = write_harness_config(
            ranked=self.chosen,
            harness_id=harness["id"],
            preference=self.preference.value,
            hardware=self.hw.to_dict(),
            output_dir=self.output_dir,
            demo=self.demo,
        )
        self.result = {
            "cancelled": False,
            "model": self.chosen.to_dict(),
            "harness_id": harness["id"],
            "preference": self.preference.value,
            "hardware": self.hw.to_dict(),
            "config_path": str(path),
        }
        self.exit(self.result)


def run_tui(
    *,
    demo: bool = True,
    output_dir: Path | None = None,
    preference: str = "Smarter",
) -> dict:
    app = MagnitudeSetupApp(
        demo=demo,
        output_dir=output_dir,
        initial_preference=Preference(preference),
    )
    return app.run() or {"cancelled": True}
