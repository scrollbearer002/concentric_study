import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";

mermaid.initialize({
  startOnLoad: false,
  theme: "base",
  themeVariables: {
    primaryColor: "#fff7d6",
    primaryTextColor: "#1d1b19",
    primaryBorderColor: "#b8892d",
    lineColor: "#4b4a47",
    secondaryColor: "#eaf3ff",
    tertiaryColor: "#e7f8e7",
    fontFamily: "Georgia, Palatino Linotype, serif",
  },
  flowchart: {
    curve: "basis",
    useMaxWidth: true,
  },
});

let lastDiagramHashes = { master: null, runtime: null };
const state = {
  payload: null,
  selectedStationId: new URLSearchParams(window.location.search).get("station"),
  selectedViewpointId: new URLSearchParams(window.location.search).get("viewpoint"),
};
let pollingHandle = null;

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function escapeAttr(value) {
  return escapeHtml(value).replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

function getSelectedStation(payload = state.payload) {
  if (!payload) return null;
  return payload.stations.find((station) => station.id === state.selectedStationId) || payload.stations[0] || null;
}

function getSelectedViewpoint(payload = state.payload) {
  if (!payload) return null;
  return payload.viewpoints.find((viewpoint) => viewpoint.id === state.selectedViewpointId) || payload.viewpoints[0] || null;
}

function selectedLaws(payload = state.payload, station = getSelectedStation(payload), viewpoint = getSelectedViewpoint(payload)) {
  if (!payload || !station || !viewpoint) return [];
  const allowed = new Set(viewpoint.law_ids || []);
  return payload.laws.filter((law) => station.law_ids.includes(law.id) || allowed.has(law.id));
}

function selectedFiles(payload = state.payload, station = getSelectedStation(payload)) {
  if (!payload || !station) return [];
  const stationFileIds = new Set(station.file_ids || []);
  return payload.files.filter((file) => stationFileIds.has(file.id));
}

function selectedTraceSteps(payload = state.payload, station = getSelectedStation(payload)) {
  if (!payload || !station) return [];
  return (payload.latest_run.trace_tail || []).filter((step) => (step.station_ids || []).includes(station.id));
}

async function renderDiagram(containerId, definition, key) {
  const hash = `${containerId}:${definition}`;
  if (lastDiagramHashes[key] === hash) return;
  const container = document.getElementById(containerId);
  const renderId = `${containerId}-${Date.now()}`;
  const { svg } = await mermaid.render(renderId, definition);
  container.innerHTML = svg;
  lastDiagramHashes[key] = hash;
}

async function renderSvgDiagram(containerId, url, key) {
  const hash = `${containerId}:${url}`;
  if (lastDiagramHashes[key] === hash) return;
  const container = document.getElementById(containerId);
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to load diagram ${url}`);
  }
  const svg = await response.text();
  container.innerHTML = svg;
  lastDiagramHashes[key] = hash;
}

async function renderDiagramSlot(containerId, key, d2Url, mermaidDefinition) {
  if (d2Url) {
    try {
      await renderSvgDiagram(containerId, d2Url, key);
      return;
    } catch (error) {
      console.warn(`D2 render failed for ${containerId}`, error);
    }
  }
  await renderDiagram(containerId, mermaidDefinition, key);
}

function syncSelectionToUrl() {
  const params = new URLSearchParams(window.location.search);
  if (state.selectedStationId) {
    params.set("station", state.selectedStationId);
  } else {
    params.delete("station");
  }
  if (state.selectedViewpointId) {
    params.set("viewpoint", state.selectedViewpointId);
  } else {
    params.delete("viewpoint");
  }
  const query = params.toString();
  const nextUrl = `${window.location.pathname}${query ? `?${query}` : ""}`;
  window.history.replaceState({}, "", nextUrl);
}

function renderViewpoints(payload) {
  const selected = getSelectedViewpoint(payload);
  const container = document.getElementById("viewpoints");
  container.innerHTML = payload.viewpoints.map((viewpoint) => `
    <button class="chip ${selected?.id === viewpoint.id ? "selected" : ""}" data-viewpoint-id="${escapeHtml(viewpoint.id)}">
      ${escapeHtml(viewpoint.name)}
      <span class="small">${escapeHtml(viewpoint.subtitle)}</span>
    </button>
  `).join("");

  container.querySelectorAll("[data-viewpoint-id]").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedViewpointId = button.getAttribute("data-viewpoint-id");
      const viewpoint = getSelectedViewpoint(payload);
      const selectedStation = getSelectedStation(payload);
      if (viewpoint && selectedStation && !viewpoint.station_ids.includes(selectedStation.id)) {
        state.selectedStationId = viewpoint.station_ids[0];
      }
      render(payload);
    });
  });
}

function renderMetricCards(payload) {
  const station = getSelectedStation(payload);
  const viewpoint = getSelectedViewpoint(payload);
  const cards = [
    { label: "Focus Station", value: station?.name || "unknown", tone: "muted" },
    { label: "Viewpoint", value: viewpoint?.name || "unknown", tone: "muted" },
    { label: "Conformance", value: payload.metrics.conformance_passed ? "Passing" : "Blocking", tone: payload.metrics.conformance_passed ? "ok" : "warn" },
    { label: "Latest Task Result", value: payload.metrics.latest_task_result || "unknown", tone: "muted" },
    { label: "Calibration Records", value: payload.metrics.calibration_records ?? "0", tone: "muted" },
    { label: "Unlabeled Packets", value: payload.metrics.calibration_unlabeled ?? "0", tone: payload.metrics.calibration_unlabeled > 0 ? "warn" : "ok" },
    { label: "Planner Actions", value: payload.metrics.planner_visible_actions ?? "0", tone: "muted" },
    { label: "Latest Run Steps", value: payload.metrics.latest_step_count ?? "0", tone: "muted" },
  ];

  document.getElementById("metric-cards").innerHTML = cards.map((card) => `
    <div class="card">
      <div class="label">${escapeHtml(card.label)}</div>
      <div class="value ${card.tone}">${escapeHtml(card.value)}</div>
    </div>
  `).join("");
}

function renderFocusSummary(payload) {
  const station = getSelectedStation(payload);
  const viewpoint = getSelectedViewpoint(payload);
  const laws = selectedLaws(payload, station, viewpoint);
  const files = selectedFiles(payload, station);
  const traceSteps = selectedTraceSteps(payload, station);

  document.getElementById("focus-summary").innerHTML = `
    <div class="focus-grid">
      <div class="focus-meta">
        <div>
          <h3>${escapeHtml(station?.name || "Unknown station")}</h3>
          <div class="metaphor">${escapeHtml(station?.metaphor || "")}</div>
          <div class="role">${escapeHtml(station?.role || "")}</div>
        </div>
        <div>
          <div class="small">Current signal</div>
          <div>${escapeHtml(station?.current_signal || "No current signal.")}</div>
        </div>
        <div>
          <div class="small">Why this viewpoint cares</div>
          <ul>${(viewpoint?.concerns || []).map((concern) => `<li>${escapeHtml(concern)}</li>`).join("")}</ul>
        </div>
      </div>
      <div class="focus-meta">
        <div>
          <div class="small">Related laws</div>
          <div class="inline-pills">
            ${laws.map((law) => `<span class="mini-pill">${escapeHtml(law.name)}: ${escapeHtml(law.status)}</span>`).join("") || '<span class="muted">None</span>'}
          </div>
        </div>
        <div>
          <div class="small">Governing files</div>
          <ul>${files.map((file) => `<li>${escapeHtml(file.path)}</li>`).join("")}</ul>
        </div>
        <div>
          <div class="small">Latest trace contact</div>
          <div>${escapeHtml(traceSteps.length)} recent step(s) in the visible trace tail.</div>
          <div class="small" style="margin-top:0.35rem;">${escapeHtml(station?.legitimacy_note || "")}</div>
        </div>
      </div>
    </div>
  `;
}

function renderStations(payload) {
  const selectedStation = getSelectedStation(payload);
  const selectedViewpoint = getSelectedViewpoint(payload);
  document.getElementById("stations").innerHTML = payload.stations.map((station) => {
    const inViewpoint = selectedViewpoint?.station_ids.includes(station.id);
    return `
      <article class="station ${selectedStation?.id === station.id ? "selected" : ""} ${inViewpoint ? "" : "dimmed"}" data-station-id="${escapeHtml(station.id)}">
        <h3>${escapeHtml(station.name)}</h3>
        <div class="metaphor">${escapeHtml(station.metaphor)}</div>
        <div class="role">${escapeHtml(station.role)}</div>
        <div class="small">Current signal</div>
        <div>${escapeHtml(station.current_signal)}</div>
        <div class="small" style="margin-top:0.45rem;">Tools / files</div>
        <ul>${station.files.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
      </article>
    `;
  }).join("");

  document.querySelectorAll("[data-station-id]").forEach((card) => {
    card.addEventListener("click", () => {
      state.selectedStationId = card.getAttribute("data-station-id");
      render(payload);
    });
  });
}

function renderLatestRun(payload) {
  const station = getSelectedStation(payload);
  const traceSteps = selectedTraceSteps(payload, station);
  const run = payload.latest_run;
  const traceTail = traceSteps.map((step) => {
    const prefix = step.index != null ? `#${step.index} ` : "";
    const action = step.action_type || "unknown";
    const status = step.status || "unknown";
    const thought = step.thought ? ` — ${step.thought}` : "";
    return `${prefix}${action} -> ${status}${thought}`;
  }).join("\n");

  document.getElementById("latest-run").innerHTML = `
    <div class="run-grid">
      <div class="kv"><div class="k">Run ID</div><div class="v">${escapeHtml(run.run_id || "unknown")}</div></div>
      <div class="kv"><div class="k">Task</div><div class="v">${escapeHtml(run.task_id || "unknown")}</div></div>
      <div class="kv"><div class="k">Outcome</div><div class="v">${escapeHtml(run.outcome || "unknown")}</div></div>
      <div class="kv"><div class="k">Task Result</div><div class="v">${escapeHtml(run.task_result || "unknown")}</div></div>
      <div class="kv"><div class="k">Final Verification</div><div class="v">${escapeHtml(run.final_verification_status || "unknown")}</div></div>
      <div class="kv"><div class="k">Duration</div><div class="v">${escapeHtml(run.duration_seconds ?? "0")}s</div></div>
      <div class="kv"><div class="k">Step Count</div><div class="v">${escapeHtml(run.step_count ?? "0")}</div></div>
      <div class="kv"><div class="k">Focused Station</div><div class="v">${escapeHtml(station?.name || "unknown")}</div></div>
    </div>
  `;

  document.getElementById("trace-tail").textContent = traceTail || "No recent trace steps matched the selected station in the visible tail.";
}

function renderRuntimeContext(payload) {
  const station = getSelectedStation(payload);
  const viewpoint = getSelectedViewpoint(payload);
  const executionFamilies = payload.dynamic_execution.execution_family_counts || {};
  const families = Object.entries(executionFamilies)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([name, count]) => `${name} (${count})`)
    .join(", ");

  document.getElementById("runtime-context").textContent =
    `${viewpoint?.name || "Viewpoint"} is currently focusing ${station?.name || "the republic"}. ` +
    `The latest runtime artifact shows dominant execution families: ${families || "none"}.`;
}

function renderConformance(payload) {
  const station = getSelectedStation(payload);
  const laws = selectedLaws(payload, station, getSelectedViewpoint(payload));
  const failures = (payload.conformance.blocking_failures || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("");
  const warnings = (payload.conformance.warnings || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("");
  document.getElementById("conformance").innerHTML = `
    <div><strong class="${payload.conformance.passed ? "ok" : "warn"}">${payload.conformance.passed ? "Conformance passing" : "Conformance blocking"}</strong></div>
    <div class="small">Focused station: ${escapeHtml(station?.name || "unknown")}</div>
    <div class="small" style="margin-top:0.4rem;">Relevant constitutional acts</div>
    <ul>${laws.map((law) => `<li>${escapeHtml(law.name)} — ${escapeHtml(law.signal)}</li>`).join("") || "<li>None</li>"}</ul>
    <div class="small" style="margin-top:0.5rem;">Blocking failures</div>
    ${failures ? `<ul>${failures}</ul>` : `<div class="ok">None</div>`}
    <div class="small" style="margin-top:0.5rem;">Warnings</div>
    ${warnings ? `<ul>${warnings}</ul>` : `<div class="muted">None</div>`}
  `;
}

function renderLegitimacy(payload) {
  const station = getSelectedStation(payload);
  const calibration = payload.calibration;
  const reviewCounts = calibration.review_state_counts || {};
  const note = station?.id === "supreme-inspectorate" || station?.id === "records-and-treasury"
    ? "This station sits directly on the legitimacy loop."
    : "This station feeds evidence into the legitimacy loop indirectly through the archive and final verification process.";

  document.getElementById("legitimacy").innerHTML = `
    <div><strong>Calibration state</strong></div>
    <div class="small">Total records: ${escapeHtml(calibration.total_records ?? 0)}</div>
    <div class="small">Review states: ${escapeHtml(JSON.stringify(reviewCounts))}</div>
    <div class="small">Human inter-rater compared: ${escapeHtml(calibration.human_inter_rater?.compared ?? 0)}</div>
    <div class="small">Latest summary mode: ${escapeHtml(calibration.mode || "unknown")}</div>
    <div class="small" style="margin-top:0.5rem;">Focused note</div>
    <div>${escapeHtml(note)}</div>
  `;
}

function renderSourcegraph(payload) {
  const station = getSelectedStation(payload);
  const files = selectedFiles(payload, station);
  const sourcegraph = payload.sourcegraph || {};
  const localIndex = sourcegraph.local_index || {};
  const stationQuery = station ? sourcegraph.station_queries?.[station.id] : null;
  const fileLinks = files.map((file) => {
    const query = sourcegraph.file_queries?.[file.id];
    if (!query) {
      return `<li>${escapeHtml(file.path)}</li>`;
    }
    const anchor = query.url
      ? `<a href="${escapeAttr(query.url)}" target="_blank" rel="noreferrer">${escapeHtml(file.path)}</a>`
      : escapeHtml(file.path);
    return `<li>${anchor}</li>`;
  }).join("");

  const stationLink = stationQuery?.url
    ? `<a href="${escapeAttr(stationQuery.url)}" target="_blank" rel="noreferrer">Open focused station search</a>`
    : `<span class="muted">No Sourcegraph URL available for this station yet.</span>`;

  document.getElementById("sourcegraph").innerHTML = `
    <div><strong>Sourcegraph bridge</strong></div>
    <div class="small">Repo: ${escapeHtml(sourcegraph.repo_name || "unknown")}</div>
    <div class="small">Base URL: ${escapeHtml(sourcegraph.base_url || "unconfigured")}</div>
    <div class="small" style="margin-top:0.45rem;">Local index signal</div>
    <div>${escapeHtml(localIndex.signal || "No index signal available.")}</div>
    <div class="small" style="margin-top:0.45rem;">Focused station query</div>
    <div><code>${escapeHtml(stationQuery?.query || "No query available.")}</code></div>
    <div class="small" style="margin-top:0.35rem;">${stationLink}</div>
    <div class="small" style="margin-top:0.45rem;">Focused files</div>
    ${fileLinks ? `<ul>${fileLinks}</ul>` : `<div class="muted">No focused files.</div>`}
  `;
}

function renderStructurizr(payload) {
  const structurizr = payload.structurizr || {};
  const exports = structurizr.exports || {};
  const tooling = structurizr.tooling || {};

  const dslLink = structurizr.workspace_dsl
    ? `<a href="${escapeAttr(structurizr.workspace_dsl)}" target="_blank" rel="noreferrer">Open workspace.dsl</a>`
    : `<span class="muted">No workspace DSL generated yet.</span>`;
  const staticLink = exports.static_index
    ? `<a href="${escapeAttr(exports.static_index)}" target="_blank" rel="noreferrer">Open static atlas export</a>`
    : `<span class="muted">Static export not available yet.</span>`;
  const jsonLink = exports.json_workspace
    ? `<a href="${escapeAttr(exports.json_workspace)}" target="_blank" rel="noreferrer">Open exported JSON workspace</a>`
    : `<span class="muted">JSON export not available yet.</span>`;
  const inspectLink = exports.inspect_report
    ? `<a href="${escapeAttr(exports.inspect_report)}" target="_blank" rel="noreferrer">Open inspect report</a>`
    : `<span class="muted">Inspect report not available yet.</span>`;

  document.getElementById("structurizr").innerHTML = `
    <div><strong>Structurizr atlas</strong></div>
    <div class="small">${escapeHtml(structurizr.signal || "No Structurizr signal available.")}</div>
    <div class="small" style="margin-top:0.45rem;">Tooling</div>
    <div>CLI: <strong class="${tooling.cli_available ? "ok" : "warn"}">${tooling.cli_available ? "available" : "missing"}</strong> · Docker: <strong class="${tooling.docker_available ? "ok" : "warn"}">${tooling.docker_available ? "available" : "missing"}</strong></div>
    <div class="small" style="margin-top:0.45rem;">Atlas bundle</div>
    <ul>
      <li>${dslLink}</li>
      <li>${staticLink}</li>
      <li>${jsonLink}</li>
      <li>${inspectLink}</li>
    </ul>
    <div class="small" style="margin-top:0.45rem;">Docs / ADRs</div>
    <div>${escapeHtml(structurizr.docs?.count ?? 0)} docs · ${escapeHtml(structurizr.adrs?.count ?? 0)} ADRs</div>
    ${structurizr.export_error ? `
      <div class="small" style="margin-top:0.45rem;">Export error</div>
      <div class="warn">${escapeHtml(structurizr.export_error)}</div>
    ` : ""}
  `;
}

function renderToolHooks(payload) {
  const station = getSelectedStation(payload);
  const observability = payload.observability || {};
  const sourcegraph = payload.sourcegraph || {};
  const structurizr = payload.structurizr || {};
  document.getElementById("tool-hooks").innerHTML = payload.tool_hooks.map((tool) => `
    <div class="tool">
      <div class="tool-name">${escapeHtml(tool.name)}</div>
      <div class="tool-state ${tool.available ? "ok" : "warn"}">${tool.available ? "Available" : "Not detected"}</div>
      <div class="small">${escapeHtml(tool.purpose)}</div>
      <div class="small" style="margin-top:0.35rem;">Launch: ${escapeHtml(tool.command || "n/a")}</div>
      ${tool.name === "Phoenix" ? `
        <div class="small" style="margin-top:0.35rem;">Telemetry: ${
          observability.enabled
            ? `enabled for ${escapeHtml(observability.project_name || "unknown project")}`
            : escapeHtml(observability.reason || "not enabled")
        }</div>
      ` : ""}
      ${tool.name === "Sourcegraph" ? `
        <div class="small" style="margin-top:0.35rem;">Repo bridge: ${
          escapeHtml(sourcegraph.signal || "No Sourcegraph bridge signal available.")
        }</div>
      ` : ""}
      ${tool.name === "Structurizr" ? `
        <div class="small" style="margin-top:0.35rem;">Atlas: ${
          escapeHtml(structurizr.signal || "No Structurizr atlas signal available.")
        }</div>
      ` : ""}
      <div class="small" style="margin-top:0.35rem;">Why it helps ${escapeHtml(station?.name || "this republic")}: ${
        escapeHtml(station?.id === "supreme-inspectorate" && tool.name === "Phoenix"
          ? "runtime traces would let the judge and the run timeline be correlated directly."
          : tool.name === "Structurizr"
            ? "it turns the control-room model into the official architecture atlas with docs, ADRs, and exportable views."
          : station?.id === "planning-ministry" && tool.name === "Sourcegraph"
            ? "semantic code graph views would tighten planner-to-runtime understanding."
            : "it can become a specialized live window attached to this control room.")
      }</div>
    </div>
  `).join("");
}

async function render(payload) {
  state.payload = payload;
  if (!state.selectedViewpointId || !payload.viewpoints.some((viewpoint) => viewpoint.id === state.selectedViewpointId)) {
    state.selectedViewpointId = payload.selection.default_viewpoint_id;
  }
  const selectedViewpoint = getSelectedViewpoint(payload);

  if (!state.selectedStationId || !payload.stations.some((station) => station.id === state.selectedStationId)) {
    state.selectedStationId = payload.selection.default_station_id;
  }
  const selectedStation = getSelectedStation(payload);
  if (selectedViewpoint && selectedStation && !selectedViewpoint.station_ids.includes(selectedStation.id)) {
    state.selectedStationId = selectedViewpoint.station_ids[0];
  }

  document.getElementById("status-pill").textContent = payload.status;
  document.getElementById("status-pill").className = `pill ${payload.conformance.passed ? "ok" : "warn"}`;
  document.getElementById("updated-at").textContent =
    `Updated ${payload.generated_at}` +
    (payload.observability?.enabled ? ` • Phoenix project ${payload.observability.project_name}` : "");

  const stationId = getSelectedStation(payload)?.id;
  const viewpointId = getSelectedViewpoint(payload)?.id;
  syncSelectionToUrl();
  const masterDiagram =
    (stationId && payload.diagrams.station_focus?.[stationId]) ||
    (viewpointId && payload.diagrams.viewpoint_focus?.[viewpointId]) ||
    payload.diagrams.master_systems;
  const masterD2 =
    (stationId && payload.diagrams.d2?.station_focus?.[stationId]) ||
    payload.diagrams.d2?.master_systems ||
    null;
  const runtimeD2 = payload.diagrams.d2?.runtime_overview || null;
  const versionSuffix = payload.generated_at ? `?v=${encodeURIComponent(payload.generated_at)}` : "";

  await renderDiagramSlot("master-diagram", "master", masterD2 ? `${masterD2}${versionSuffix}` : null, masterDiagram);
  await renderDiagramSlot("runtime-diagram", "runtime", runtimeD2 ? `${runtimeD2}${versionSuffix}` : null, payload.diagrams.runtime_overview);
  renderViewpoints(payload);
  renderMetricCards(payload);
  renderFocusSummary(payload);
  renderStations(payload);
  renderRuntimeContext(payload);
  renderLatestRun(payload);
  renderConformance(payload);
  renderLegitimacy(payload);
  renderSourcegraph(payload);
  renderStructurizr(payload);
  renderToolHooks(payload);
}

async function refresh() {
  const response = await fetch("/api/state");
  const payload = await response.json();
  await render(payload);
}

function startPollingFallback() {
  if (pollingHandle) return;
  const tick = async () => {
    try {
      await refresh();
    } catch (error) {
      document.getElementById("status-pill").textContent = "Polling fallback";
      document.getElementById("status-pill").className = "pill warn";
      document.getElementById("updated-at").textContent = error.message;
    } finally {
      pollingHandle = window.setTimeout(tick, 5000);
    }
  };
  void tick();
}

async function startEventStream() {
  try {
    await refresh();
  } catch (error) {
    startPollingFallback();
    return;
  }

  if (!("EventSource" in window)) {
    startPollingFallback();
    return;
  }

  const source = new EventSource("/api/events");
  source.addEventListener("snapshot", async (event) => {
    const payload = JSON.parse(event.data);
    await render(payload);
  });
  source.onerror = () => {
    source.close();
    startPollingFallback();
  };
}

void startEventStream();
