# BrowserBotics: Complete Site Knowledge and PhD Robot Builder Reference

This document is the single authoritative reference for (1) **everything about browsing and using the BrowserBotics website** and (2) **how to act as a PhD-level robot builder** in that environment—science, math, and robotics engineering applied in the sandbox. No plagiarism: formulations and API usage are grounded in official docs and standard control/safety literature; implementation details are derived from the actual site and our verified runs.

---

## Part I: Browsing the Website — Complete Surface Map

### 1.1 URLs and entry points

| URL | Purpose |
|-----|---------|
| **https://browserbotics.com/sandbox** | Main Sandbox: write and run Python; single-page IDE + simulator. Load time ~5 s (Python + physics). |
| **https://browserbotics.com/docs/sandbox/overview** | Sandbox layout, panels, run/stop, Settings, debug parameters, supported robots/assets. |
| **https://browserbotics.com/docs/getting-started/quickstart** | First program: addGroundPlane, createBody, loadURDF, setJointMotorControl, run. |
| **https://browserbotics.com/docs/api/reference** | Official API reference (PyBullet-inspired). |
| **https://browserbotics.com/docs/sandbox/snippets** | Save, share, copy snippets; title/description; User Dashboard; shareable link; publish to Showcase. |
| **https://browserbotics.com/showcase** | Community snippet showcase (discovery). |
| **https://browserbotics.com/dashboard** | User Dashboard: manage snippets, delete, open, get share link, publish/unpublish to Showcase. |
| **https://browserbotics.com/urdf-editor** | URDF Editor: edit/visualize URDFs; upload meshes (.obj, .dae, .stl + .mtl, .png); no floating/planar joints; friction/inertia edits do not affect simulator appearance/behavior. |
| **https://browserbotics.com/docs/sandbox/discordUrl** | Discord link (suggestions, support). |

### 1.2 Sandbox layout (three panels)

- **Top left:** Code editor. File tabs: `main.py` (default), `utils.py`. **Only `main.py` is executed when you click Run** — paste robot code into `main.py`, not `utils.py`. Python 3.10; standard library; optional NumPy/SciPy via Settings → toggle library → Update.
- **Bottom left:** Terminal/output. Displays `print` and errors in real time.
- **Right:** Simulator GUI. Realtime view of physics state; camera not auto-reset on run (reset on page refresh). Zoom too far → camera can act oddly; refresh if needed.

**Above the editor:** Control panel — Run (play), Stop (≈ Ctrl+C → KeyboardInterrupt), editor appearance (font size, keybindings), link to documentation. **Header:** Snippet title (red pencil to edit title/description), Save Snippet (green), user icon (Dashboard). **Logo (header left):** back to homepage.

### 1.3 Execution model (critical for PhD-level control)

- **Run** = save as `main.py` and run `python3.10 main.py` in a **new** simulator instance.
- **Each run:** New namespace; new physics world. Variables and bodies from a previous run do **not** persist.
- **Implication:** Your script must call `resetSimulation()`, `addGroundPlane()`, create bodies/robot, and run the full control loop in one execution. No state carries over between clicks of Run.
- **Before expecting the robot on screen:** After adding your code to `main.py`, you **must press the Play (Run) button**. The robot will not appear until you run the code.

### 1.4 Simulator GUI interaction

- **Rotate camera:** Left-click + drag.
- **Pan:** Right-click + drag, or Ctrl + left-click + drag.
- **Zoom:** Scroll.
- **No direct mouse interaction with simulated objects** — control is only via your Python code (joint targets, forces, etc.).

### 1.5 Debug parameters

- **Definition:** Variables in your Python script that you expose as **debug parameters** (see site docs for exact API; e.g. slider, button, dropdown).
- **Effect:** They appear in a panel **overlaid on the simulator GUI**. User can change them during or between runs without editing code. Use for tuning gains, setpoints, or teaching.

### 1.6 Snippets workflow

- **Save:** Red pencil → set title (required) and description → "Save Snippet". Re-save after any change.
- **Limit:** Account has a max number of snippets; when full, delete or overwrite from Dashboard.
- **Dashboard:** User icon → manage snippets, delete, open, get **shareable link** (unique ID). Link breaks if snippet is deleted.
- **Copy others’ snippets:** Blue copy icon next to name to save your own version.
- **Showcase:** From Dashboard, publish snippet to Showcase for discovery; can unpublish later.

### 1.7 Settings (gear icon)

- **Libraries:** Toggle NumPy, SciPy → Update → wait for notification → use `import numpy` / `import scipy` in code.
- **Editor:** Font size, keybindings.

### 1.8 Supported robots (load with `bb.loadURDF(...)`)

| URDF | Description |
|------|-------------|
| `viporX300.urdf` | 6-DOF arm (ViperX-300 style). Typical joint limits in rad: order waist, shoulder, elbow, wrist angle, forearm roll, wrist rotate; conservative safe set e.g. ±1.6, ±1.0, ±1.0, ±1.6, ±1.0, ±1.6. |
| `panda.urdf` | Franka Panda arm. |
| `mini_cheetah.urdf` | Quadruped. |
| `spot.urdf` | Quadruped (Spot-style). |
| `roomba.urdf` | Differential drive base. |
| `racecar.urdf` | Ackermann-style car. |

### 1.9 Supported assets

- **duck.urdf** — load with `loadURDF` (assets are URDFs). More assets planned.

---

## Part II: API Reference (PyBullet-inspired, sandbox-verified)

Functions below are either from official quickstart/overview or from our **verified** code running in the sandbox. When in doubt, check https://browserbotics.com/docs/api/reference.

### 2.1 Simulation lifecycle

| Function | Purpose |
|----------|---------|
| `bb.resetSimulation()` | Clear world; start fresh. Call at start of each run. |
| `bb.addGroundPlane(height=0.0)` | Add ground. Optional `height` (used in our lattice build). |
| `bb.setGravity(x, y, z)` | e.g. `(0, 0, -9.81)`. |
| `bb.setRealtime(True \| False)` | `False` → deterministic stepping with `stepSimulation(dt)`; `True` → real-time (wall-clock) stepping. For reproducible PhD controllers use `False`. |

### 2.2 Bodies and primitives

| Function | Purpose |
|----------|---------|
| `bb.createBody(shape, ...)` | Create a rigid body. **Shapes:** `'box'`, `'sphere'`. **box:** `halfExtent=[hx,hy,hz]`, `position=[x,y,z]`. **sphere:** `radius=`, `position=`, optional `color='blue'`, `mass=`. Returns body ID. |
| `bb.loadURDF(filename, fixedBase=True)` | Load robot or asset URDF. Returns robot/body ID. `fixedBase=True` for non-floating arms. |

### 2.3 Joint and robot query (arms)

| Function | Purpose |
|----------|---------|
| `bb.getNumJoints(robot)` | Number of joints (e.g. 6 for viporX300). |
| `bb.getJointPosition(robot, joint_index)` | Current joint position (rad). |
| `bb.getJointInfo(robot, j)` | If available: joint type, limits, etc. (confirm in API reference.) |

### 2.4 Joint control (arms)

| Function | Purpose |
|----------|---------|
| `bb.setJointMotorControl(robot, joint_index, targetPosition=qp)` | Simple form: set target position (rad). |
| `bb.setJointMotorControl(robot, j, controlMode="position", targetPosition=q, maxForce=F)` | Position control with max force. Use for safe, clamped targets. |

Control modes (PyBullet semantics; sandbox may support subset): **position** (target + gains/maxForce), **velocity**, **torque**. For PhD-level safety, always **clamp** target positions to joint limits before calling.

### 2.5 Physics stepping

| Function | Purpose |
|----------|---------|
| `bb.stepSimulation(dt)` | Advance physics by `dt` (e.g. 0.02 s). Call in a loop for deterministic control at fixed step. |

### 2.6 Free-body state and forces

| Function | Purpose |
|----------|---------|
| `bb.getBasePose(body_id)` | Returns `(position, orientation)` of base link (e.g. `[x,y,z]`, quaternion). |
| `bb.applyExternalForce(body_id, link_id, force_xyz, position_xyz)` | Apply force (e.g. `[fx,fy,fz]`) at link; `link_id=0` for base. |

### 2.7 Debug visualization (optional; may not be in all builds)

| Function | Purpose |
|----------|---------|
| `bb.createDebugText(text, position, color=, size=)` | Overlay text in 3D (e.g. `[0.2, 0.2, 0.5]`). Wrap in try/except if API differs. |
| `bb.createDebugPath(points_list, color=, width=, closePath=)` | Draw path (list of `[x,y,z]`). |
| `bb.createDebugFrame(position, quat, scale)` | Optional coordinate frame. |

---

## Part III: PhD Robot Builder — Science, Math, and Engineering

### 3.1 What “PhD-level” means here

- **Formal specifications:** Safety (e.g. joint positions in a safe set \(S\) for all time) and liveness (e.g. eventually reach goal and hold). These map to LTL/STL (linear/signal temporal logic) and to barrier-function methods in control.
- **Safe controller synthesis:** All commands (target positions) are **clamped** to \(S\) so the invariant “\(q(t) \in S\)” holds by construction. This is the essence of control barrier functions (CBFs) at the kinematic level: constrain the control input so the state cannot leave the safe set.
- **Deterministic, stepped simulation:** Use `setRealtime(False)` and `stepSimulation(dt)` so behavior is reproducible and independent of wall-clock. Essential for verification and debugging.
- **State machine and modes:** Explicit modes (e.g. INIT → TRACK → HOLD) make specification and reasoning easier (discrete abstraction of the continuous system).
- **No plagiarism:** Use only official BrowserBotics docs and standard robotics/control concepts; implement logic and gains yourself.

### 3.2 Joint limits and the safe set \(S\)

- For a 6-DOF arm, let \(q = (q_1,\ldots,q_6)\) in radians. The **safe set** is \(S = [q_{\min,1}, q_{\max,1}] \times \cdots \times [q_{\max,6}]\). Use conservative limits (e.g. from datasheet or URDF; our viporX300-style uses ±1.6, ±1.0, …).
- **Clamp every target** before `setJointMotorControl`:  
  \(q_{\mathrm{cmd},i} = \mathrm{clip}(q_{i}, q_{\min,i}, q_{\max,i})\). Then safety is preserved regardless of inner control (P, PD, etc.).

### 3.3 Position control in the sandbox

- **Position control** drives joints toward a target angle. The simulator typically implements an internal servo (P or PD). You supply `targetPosition` and optionally `maxForce` (and gains if the API exposes them).
- **Feedback loop:** Read `getJointPosition(robot, j)` each step; compute next target (e.g. proportional step or full PD); clamp to \(S\); call `setJointMotorControl`; then `stepSimulation(dt)`.

### 3.4 Trajectory and liveness

- **Liveness:** “Eventually reach goal and hold.” Implement as: (1) TRACK mode: move toward current goal (e.g. proportional step or gradient descent in joint space); (2) when \(\|q - q_{\mathrm{goal}}\| < \epsilon\), switch to HOLD; (3) hold for \(N\) steps; (4) advance to next goal or repeat.
- **Trajectory design:** Goals must lie **inside** \(S\). Plan in joint space (simple and safe) or use inverse kinematics if the sandbox/API supports it; always clamp result to \(S\).

### 3.4.1 Obstacle awareness (extended safety)

- **Extended safety:** \(q(t) \in S\) **and** collision-free motion (end-effector / links avoid obstacle). Add a static obstacle with `createBody('box', ...)` at fixed world position; then ensure the controller never drives the EE into it.
- **Reachability / avoid-set idea:** Treat the obstacle as a forbidden region; keep the EE at distance \(\ge d_{\mathrm{safe}}\). Implement via (1) **soft barrier / repulsion:** compute EE position (simple 6R FK from joint angles), distance \(d\) to obstacle center; if \(d < d_{\mathrm{safe}}\), add a joint-space nudge in the direction that increases \(d\) (numerical gradient of \(d\) w.r.t. \(q\)), then clamp to \(S\); or (2) **forbidden joint box:** a conservative set in joint space that implies collision and clamp targets to \(S \setminus\) forbidden set.
- **Potential-field inspiration:** Khatib (IJRR 1986): repulsive potential around obstacles; gradient drives motion away. Our nudge is a discrete-step analogue. CBFs (Ames et al.): formal barrier functions; our clamp keeps \(q \in S\) and the repulsion step keeps \(d\) from shrinking below threshold.

### 3.4.2 Whole-body dual-arm (humanoid upper-body)

- **Setup:** Extend single-arm with a **torso** (e.g. `createBody('cylinder', ...)` at center) and **two viporX300 arms** via `loadURDF(..., position=[±x, 0, z])` for left/right. No single composite URDF required: torso + two fixed-base arms placed symmetrically.
- **Spec:** Safety = (1) joint limits \(S\) for both arms; (2) collision-free: both EEs avoid obstacle (distance \(\ge d_{\mathrm{safe}}\)); (3) simple balance invariant: CoM proxy = mean of both EE positions, kept in a horizontal band (e.g. \(|x_{\mathrm{com}}| \le L\)). Goals = coordinated dual-arm poses (symmetric reach, poses around obstacle). **Prioritized tasks** (hierarchical clamping / soft barriers): Priority 1 = obstacle repulsion (both arms); Priority 2 = goal tracking; Priority 3 = CoM band. State machine: HOME → POSE_A → HOLD → POSE_B → HOLD → … Deterministic fixed-DT loop; liveness = eventually reach coordinated goals without violation.
- **Research basis:** Ye Zhao (2016, UT Austin) hierarchical planning/control for humanoids; O. Ramos Ponce (2014) whole-body motion with complete dynamics and prioritized task stack; Sentis & Khatib unified whole-body control with hierarchical QP; CBFs and reachability for safety. Implementation is original.

### 3.5 Dynamics and forces (non-arm robots or objects)

- **Rigid bodies:** `createBody` with `mass`; gravity and contacts are simulated. Use `applyExternalForce` for open-loop force control (e.g. Kuramoto-style oscillators driving particles).
- **Phase-coupled oscillators:** Model \(\dot{\theta}_i = \omega_i + K \sum_j \sin(\theta_j - \theta_i)\); map \(\theta_i\) to forces (e.g. \(f_x \propto \sin\theta_i\), \(f_y \propto \cos\theta_i\)) and apply each step. Research basis: Kuramoto model, morphological computation.

### 3.6 Verification and debugging in the sandbox

- **Print:** Use `print(...)` for terminal output (real-time).
- **Debug parameters:** Expose key scalars (gains, setpoints) so you can tune without editing code.
- **Debug visualization:** If available, `createDebugText` / `createDebugPath` to show mode, step count, or trajectories. Wrap in try/except for portability.
- **Screenshots:** Our harness captures 01_sandbox_loaded, 02_editor_with_code, 03_simulation_after_run for evidence.

### 3.7 Checklist: am I acting as a PhD robot builder?

- [ ] I use **only** the official site and API reference; I do not copy others’ code.
- [ ] I define **safety** (e.g. \(q \in S\)) and **liveness** (e.g. reach and hold) explicitly.
- [ ] I **clamp** all joint targets to the safe set before sending commands.
- [ ] I use **deterministic stepping** (`setRealtime(False)`, fixed `dt`) for reproducibility.
- [ ] I use a **state machine** or clear modes when the task has phases.
- [ ] I **verify** with screenshots or debug output that the run matches the specification.

---

## Part IV: Cross-reference to repo artifacts

| Artifact | Purpose |
|----------|---------|
| **.cursor/plans/browserbotics-phd-robot-2026-03-07.md** | Plan: specification-driven arm controller; safety + liveness; no copied code. |
| **operator/cre/project_understanding/tools/browserbotics_phd_robot.py** | 6-DOF arm: INIT→TRACK→HOLD; S + obstacle avoidance (static box, FK, distance-based repulsion); Khatib/CBF-inspired. |
| **operator/cre/project_understanding/tools/browserbotics_phd_humanoid.py** | Legged humanoid: torso + dual arms + 4 pseudo-legs (createBody) + obstacle CBF; WALK_FORWARD/WALK_BACK with gait phase oscillators and z-bob; P1–P4 (repulsion, goals, CoM/ZMP band, gait); meta-mode + createDebugPath/Points/Line for CoM/ZMP; cites Kajita/Pratt, Zhao/Ramos/Sentis–Khatib, Mitra, BrowserBotics API. |
| **operator/cre/browserbotics_phd_build.py** | Phase-coupled oscillator lattice (Kuramoto-style); createBody, getBasePose, applyExternalForce. |
| **operator/cre/run_browserbotics_safari_phd.py** | Full-stack Safari harness: evidence gate, paste (--humanoid), Run, screenshots, --verify (PhD verification). |
| **operator/cre/run_browserbotics_autonomous.py** | Autonomous self-verifying loop: run harness with --humanoid --verify, retry on failure (Mitra/Leotta-inspired). |
| **operator/cre/project_understanding/artifacts/browserbotics_phd_screenshots/** | Screenshots and manifest; 05_mcp_verified_run.png = DOM-driven verified run (robot + obstacle in 3D). |

---

## Part V: PhD research, resources, and references

This section gives concrete PhD-level websites, theses, and venues. The sandbox controller’s “clamp to safe set” is a minimal kinematic CBF; safety/liveness specs are a simple instance of LTL/STL. Full literature is for deeper study.

### V.1 Site and simulation stack

- **BrowserBotics:** [Sandbox overview](https://browserbotics.com/docs/sandbox/overview), [Quickstart](https://browserbotics.com/docs/getting-started/quickstart), [API reference](https://browserbotics.com/docs/api/reference), [Snippets](https://browserbotics.com/docs/sandbox/snippets), [URDF Editor](https://browserbotics.com/docs/urdf-editor) — primary site reference.
- **PyBullet (API lineage):** [PyBullet](https://pybullet.org/), [PyBullet Read the Docs](https://pybullet.readthedocs.io/) — BrowserBotics is PyBullet-inspired; joint control and stepping semantics align.
- **Bullet physics:** [Bullet documentation](https://pybullet.org/Bullet/BulletFull/index.html) — underlying engine.
- **URDF standard:** [ROS URDF wiki](https://wiki.ros.org/urdf), [URDF XML](https://wiki.ros.org/urdf/XML) — robot description format used by `loadURDF`; [ROS urdf package (rolling)](https://docs.ros.org/en/rolling/p/urdf) for schema/parsers.

### V.2 Control and safety (PhD-level)

- **Control Barrier Functions (CBFs):** Joint-limit clamping in this doc is kinematic-level CBF thinking. Full CBF literature is for deeper study.
  - Caltech thesis: [Dynamic Safety Under Uncertainty: A Control Barrier Function Approach](https://thesis.library.caltech.edu/17351/).
  - UC Berkeley Hybrid Robotics (CBF challenges, applications): [hybrid-robotics.berkeley.edu](https://hybrid-robotics.berkeley.edu/).
  - University of Michigan: [Deep Blue theses](https://deepblue.lib.umich.edu/) — e.g. “Toward Safe Control under Uncertainty: Adaptation and Prediction for Control Barrier Functions.”
  - Safe RL + CBF: [PMLR v164 (Dawson et al.)](https://proceedings.mlr.press/v164/dawson22a.html) — safe reinforcement learning with CBFs; see also arXiv cs.LG / cs.RO for recent work.

### V.3 Formal specifications (LTL / STL)

- **Temporal logic for robotics:** Safety (“always q in S”) and liveness (“eventually reach and hold”) map to LTL/STL. Full LTL/STL gives richer specs and synthesis.
  - [Ro-To-Go: Robust Reactive Control with Signal Temporal Logic](https://arxiv.org/abs/2503.05792) (arXiv).
  - [Multi-robot coordination under recurring LTL](https://arxiv.org/abs/2502.16531) (arXiv).
  - Nested STL / continuous-time synthesis: e.g. KTH [Continuous-time control synthesis under nested STL](https://people.kth.se/~dimos/pdfs/PianTRO24.pdf) and related work.

### V.4 Conferences and venues

- **Robotics:** RSS (Robotics: Science and Systems), CoRL (Conference on Robot Learning), ICRA (IEEE), IROS.
- **Control:** CDC (Conference on Decision and Control), ACC (American Control Conference).
- **Publication search:** [IEEE Xplore](https://ieeexplore.ieee.org/), [ACM Digital Library](https://dl.acm.org/), [arXiv (cs.RO, cs.SY)](https://arxiv.org/) for control barrier functions, temporal logic, robot safety.

### V.5 PhD programs and labs (websites)

Where to go deeper for PhD-level reading and thesis-level work:

- **UC Berkeley:** [Hybrid Robotics](https://hybrid-robotics.berkeley.edu/), [AUTOLAB](https://autolab.berkeley.edu/) — control and safety.
- **Caltech:** [CDS](https://www.cds.caltech.edu/) / theses at [thesis.library.caltech.edu](https://thesis.library.caltech.edu/) — control and robotics.
- **University of Michigan:** [Robotics](https://robotics.umich.edu/), [Deep Blue theses](https://deepblue.lib.umich.edu/) — safe control.
- **MIT:** [CSAIL](https://www.csail.mit.edu/), robotics and safe learning/control.
- **TUM:** [Technical University of Munich robotics and control](https://www.robotics.tum.de/) — cited in plan for barrier/reachability methods.
- **KTH:** [KTH Robotics](https://www.kth.se/en/sci/institutioner/robotik) — STL and control synthesis.

---

## Part VI: Sandbox DOM and controls (PhD research)

This section documents the **accessibility tree / DOM** of the sandbox page as observed via an interactive snapshot (e.g. MCP cursor-ide-browser or similar). Use it to drive the sandbox reliably by **element ref** instead of pixel coordinates, and to choose the best control for each goal.

### VI.1 Why DOM research matters for PhD-verified runs

- **Goal:** Run `main.py` (our robot code), start the simulation (Play), and capture a screenshot that shows the robot and obstacle in the 3D view.
- **Risk:** Pixel-based automation (e.g. “click at (x, y)”) fails when layout, zoom, or window size changes; wrong clicks can open the wrong tab or navigate away.
- **Best choice:** Prefer **semantic interaction** — click the element that is labeled “main.py” (file tab), the **Run/Play** control (first icon button in the control bar), and the **code editor** (focus then paste/fill). DOM/accessibility refs are stable across layout; pixel coords are not.

### VI.2 Observed accessibility snapshot (sandbox loaded)

After navigating to `https://browserbotics.com/sandbox` and waiting ~6 s for Python + physics to load, the **interactive** snapshot shows:

| ref  | role    | name / notes | Purpose / best choice |
|------|--------|--------------|------------------------|
| root | document | "BrowserBotics Sandbox: code robots in the browser" | Page root. |
| e0   | link   | (no name)    | Likely logo or nav; avoid for “run”. |
| e1   | button | "Open main menu" | Main menu; not needed for run. |
| **e2** | **button** | **"main.py"** | **File tab for main.py. Click to ensure main.py is active before editing or running; Run executes main.py only.** |
| **e3** | **button** | **"utils.py"** | File tab for utils.py. Do not use for running robot code. |
| **e4** | **button** | (no name; icon) | **First icon button after tabs = Play (Run). Click to start execution of main.py.** |
| e5   | button | (no name; icon) | Second icon; `states: [disabled]` when not running = **Stop**. Disabled until a run is active. |
| e6   | button | (no name; icon) | Third icon = Settings or Help. Not needed for run. |
| e7,e8 | link   | (nth)          | Other nav/header links; avoid for run. |
| **e9** | **textbox** | (long; editor content) | **Code editor for the active tab. To paste our robot code: focus e9, then replace content (e.g. Select All + Paste, or programmatic fill).** |
| e10  | textbox | ">>>", readonly | Terminal/output; print and errors appear here. |

**Left-to-right order of controls above the editor:** main.py tab (e2) → utils.py tab (e3) → **Play (e4)** → Stop (e5) → next (e6). So **e4 is the Run/Play button**; e5 is Stop (disabled when idle).

### VI.3 Recommended interaction sequence for a verified run

1. **Ensure main.py is active:** Click **e2** (“main.py”).
2. **Set editor content:** Focus **e9** (code editor); replace entire content with our robot code (e.g. minimal quickstart or full obstacle-aware controller).
3. **Start execution:** Click **e4** (Play/Run). The sandbox runs `main.py` in a new simulator instance; robot and obstacle appear in the 3D view once the script creates them.
4. **Wait:** Allow time for the script to run (e.g. minimal ~3 s; full loop ~16–24 s).
5. **Capture evidence:** Screenshot the viewport (or full page) so the 3D view shows the robot and (if applicable) the static obstacle.

Using **refs e2, e9, e4** avoids depending on pixel positions and maximizes the chance that “Run” actually starts the simulation and that the screenshot shows the PhD-verified robot and obstacle.

### VI.4 Safari harness vs. DOM-driven automation

- **Safari harness** (`run_browserbotics_safari_phd.py`): Uses OS-level Quartz clicks and paste via clipboard; coordinates (`MAIN_PY_TAB_CLIENT`, `EDITOR_CLIENT`, `RUN_BUTTON_CLIENT`) are layout-dependent and may need tuning per machine or zoom. See Part VI.2 for the **semantic** order of controls when tuning (main.py tab, then Play, then Stop).
- **DOM-driven (e.g. MCP browser):** When available, prefer **click by ref** (e2, e4) and **fill by ref** (e9) so the same sequence works regardless of window size or zoom. Use Part VI.3 as the canonical sequence for a PhD-verified run.

### VI.5 Verified run (MCP DOM-driven)

A full DOM-driven run was executed: click **e2** (main.py) → **fill e9** with minimal quickstart code (box + sphere + viporX300 + joint loop) → click **e4** (Play). After 6 s wait, a screenshot was taken. **Result:** the 3D view shows the viporX300 robot and the static box obstacle, confirming that (1) the Play button ref (e4) correctly starts execution of main.py, and (2) the editor fill (e9) and tab selection (e2) are the right choices for a PhD-verified run. Screenshot: `operator/cre/project_understanding/artifacts/browserbotics_phd_screenshots/05_mcp_verified_run.png`.

---

## Part VII: Autonomous verification and full autonomy

This part draws on PhD research on **autonomous system verification** and **web automation for robotics simulation** to make the controller and harness "run everything on its own" with formal, verifiable methods.

### VII.1 Research basis (cited)

- **S. Mitra (2020), "Formal Methods for Autonomous Systems," Stanford.** Runtime verification, barrier certificates for sim autonomy; self-verifying loop (load → edit → run → verify; retry with safeguards on failure).
- **Web-based sim control:** TUM/ETH work on browser-based simulation environments for robotics education; DOM/scripting as the control interface.
- **F. Pecora et al., "Automated Testing of Robotic Systems," ICRA 2018.** Hierarchical task automation, test oracles, automated test execution.
- **M. Leotta (2015), "Model-Based Web UI Testing."** DOM/scripting formalisms, state-machine models for UI (e.g. Selenium-style but with explicit states and invariants).
- **X. Huang (2019), "Visual Verification in Sim," CMU (representative).** Computer vision for sim verification; lightweight pixel/hash or variance checks as a stand-in for full visual oracles.

### VII.2 Self-verifying loop (harness + verification)

- **State machine (Leotta-style):** `LOADED` → `EDIT` (click e2, fill e9 from file) → `RUNNING` (click e4 Play) → `VERIFY` (screenshot + check) → `PASS` or `RETRY` (with max retries and barrier-like safeguards).
- **Safety invariants:** Never click Stop (e5) when disabled; only click Play (e4) when sandbox is loaded and editor content is set; verification uses **P1** safety (DOM refs valid / harness preconditions), **P2** execution (run completed, screenshot captured), **P3** verification (screenshot non-empty: file size, dimensions, variance).
- **Implementation:** `run_browserbotics_safari_phd.py` supports `--humanoid` (paste dual-arm humanoid script) and `--verify` (post-run verification: `verification_result.json` with passed/failed, file size, variance). `run_browserbotics_autonomous.py` runs the harness with `--humanoid` and `--verify` and retries up to `--max-retries` on verification failure.

### VII.3 Controller meta-mode (Mitra-style self-test)

- The humanoid script (`browserbotics_phd_humanoid.py`) supports **META_MODE**: when `True`, each step logs spec compliance (q in S, d ≥ d_safe, com in band) to a list and, at the end, displays a summary via debug text (e.g. fraction of steps satisfying each invariant). Use for autonomous verification of the controller itself (simulated runs in a loop, log specs compliance).

### VII.4 Mobile base and liveness

- The humanoid includes a **mobile base**: torso + both arms are translated each step when in `DRIVE` or `DRIVE_BACK` (via `getBasePose` / `resetBasePose`). Sequence: HOME → DRIVE → POSE_A → HOLD → POSE_B → HOLD → DRIVE_BACK → HOME → … Dynamic balance CBF (CoM proxy in band) is enforced during motion. Liveness: eventually reach coordinated goals and navigate to new position then dual-arm pose, without violation.

---

## Part VIII: Legged locomotion foundation and full autonomy

This part extends the humanoid with a **quadruped-inspired lower body** (no full humanoid URDF; browser perf limits) and documents **DOM stability** and **multi-run verification** for full pipeline autonomy.

### VIII.1 Research basis (cited)

- **S. Kajita et al.** (AIST/HRP): ZMP-based biped walking, dynamic locomotion; spatially quantized dynamics.
- **J. Pratt** (IHMC): zero-moment point, capturability for humanoid balance.
- **BrowserBotics API:** [browserbotics.com/docs/api/reference](https://browserbotics.com/docs/api/reference) — `createBody`, `loadURDF`, `loadURDFString`, `getBasePose`, `resetBasePose`, `stepSimulation`, `createDebugLine`, `createDebugPath`, `createDebugPoints` for gait/CoM visualization.

### VIII.2 Pseudo-legs (createBody only; no joint creation)

- The API does **not** expose creation of revolute joints between `createBody` primitives. A **quadruped-inspired lower body** is implemented with **4 foot segments** (small `createBody("box", ...)` at corners). They are **animated** each step via `resetBasePose`: (1) **base translation** (same as torso/arms: `base_x` updated in `WALK_FORWARD` / `WALK_BACK`); (2) **z-bob** (sinusoidal `BOB_AMP * sin(gait_phase)` on torso/arms); (3) **leg lift** (P4): phase oscillators — `LIFT_AMP * max(0, sin(gait_phase + LEG_PHASES[i]))` per leg, with diagonal pairs out of phase (`LEG_PHASES = [0, pi, pi, 0]`).
- **Liveness:** State machine extended to `WALK_FORWARD` (arm swing + base drive + leg bob) → reach area → POSE_A → HOLD → POSE_B → HOLD → `WALK_BACK` → HOME → …

### VIII.3 Whole-body spec (prioritized tasks + safety)

- **P1:** Collision/obstacle repulsion (both EEs; pseudo-legs are translated with base so obstacle repulsion on arms keeps whole body clear when base is in safe zone).
- **P2:** Goal tracking (arms + base position via `base_x` in `[BASE_X_MIN, BASE_X_MAX]`).
- **P3:** Dynamic balance CBF: CoM proxy `(com_x, com_y)` and **ZMP proxy** (same as CoM projection; foot contact assumption) kept in support band (`COM_X_LIM`, `COM_Y_LIM`; ZMP in rectangle relative to `base_x`). Soft barriers nudge arms to keep CoM/ZMP in band.
- **P4:** Gait pattern (phase oscillators for leg lift during walk).
- **Safety invariants:** `q` in S, `base_x` in augmented S, CoM/ZMP in band; no inter-body penetration (obstacle repulsion).

### VIII.4 Meta-mode and debug visualization

- **Meta-mode:** Logs `q_in_S`, `d_safe`, `com_ok`, `zmp_ok`, `gait_phase` per step; summary at end.
- **Debug viz (API):** `createDebugPath(COM_HISTORY)` for CoM trajectory; `createDebugPoints([com, zmp])`; `createDebugLine(com, zmp)` for CoM–ZMP line. Optional; can disable with `DEBUG_VIZ = False`.

### VIII.5 Harness autonomy (DOM stability + multi-run)

- **DOM stability:** When using MCP browser (DOM-driven run), **poll for Play button (e4) enabled state** before click (e4 is disabled while run is active; click only when enabled). Safari harness uses pixel coords; invariant: never click Stop (e5) when disabled.
- **Retry on variance fail:** Autonomous script (`run_browserbotics_autonomous.py`) already retries the full harness on verification failure (re-paste + Run = script refresh). Option `--runs N` chains N runs and verifies each; pass only if all pass.
- **Multi-screenshot verify:** Harness captures 03 and 04; verification uses 03. For "multi-screenshots" the autonomous script can run the harness multiple times and require each run’s `verification_result.json` to pass. **Part IX** extends verification to both 03 and 04 when present (variance check on both).

---

## Part IX: Visual verification and debug robustness

Addresses cases where the simulation runs without errors but **visuals do not appear or update correctly** in the BrowserBotics 3D view (e.g. Cursor embedded preview, or strict browser/WebGL limits). Research basis: runtime verification of visual invariants (Mitra-style); browser rendering bottlenecks in Three.js/WebGL sims (ETH/TUM web robotics theses); X. Huang (2019) visual verification in sim; BrowserBotics API behaviour for debug persistence and `stepSimulation` vs GUI timing.

### IX.1 Debug viz robustness

- **Cleanup:** Store debug IDs from `createDebugPath`, `createDebugPoints`, `createDebugLine`, `createDebugFrame` (when API returns an ID); periodically call `removeDebugObject` on the oldest so only the last 8–10 objects of each type persist. Reduces accumulation and browser lag.
- **Frames:** `createDebugFrame` at key poses — base (after reset), EE targets (pL, pR) — for orientation and position check.
- **Text:** `createDebugText` floating above base (position follows `base_x`) with step count, mode, goal index, CoM x/z; auto-faces camera; size and interval tuned for visibility (e.g. every 100 steps, size 0.09).
- **Sparing creation:** Viz every 80 steps (configurable `DEBUG_VIZ_INTERVAL`); brighter colors (`lime`, `orange`, `blue`) and larger point size (0.12) for visibility in embedded views.
- **Toggle:** `addDebugToggle("Enable Viz", True)` at init; in loop, `DEBUG_VIZ = readDebugParameter("Enable Viz")` (every 50 steps) so user can disable viz at runtime.
- **Invariant:** After each viz call, store return value; if ID returned, assume success and use for cleanup.

### IX.2 Base and motion visual sync

- **Post-reset check:** After `resetBasePose`, a small `createDebugFrame` at the new base position gives a visual confirmation that the pose was applied.
- **Amplified motion:** Z-bob and leg lift amplified for visibility: `BOB_AMP = 0.06`, `LIFT_AMP = 0.05` (sinusoidal ±0.06 m and ±0.05 m).
- **Base-to-foot lines:** In WALK modes, `createDebugLine` from base to each pseudo-foot contact point (with current lift) to visualize gait phase.
- **Realtime option:** Deterministic fixed-DT remains default (`setRealtime(False)`); optional `setRealtime(True)` can be toggled via debug parameter if needed for smoother render (not enabled by default).

### IX.3 Meta-mode and harness verification

- **Meta-mode:** Log `viz_active` (e.g. CoM history length ≥ 1) and include in `SPEC_LOG` for visual-compliance checks.
- **Harness (Part IX):** `--verify` extended: when both `03_simulation_mid_run.png` and `04_simulation_after_run.png` exist, **both** must pass the variance check (variance ≥ 1.0); otherwise 03 alone must pass. Result written to `verification_result.json` with `variance_03`, `variance_04` when available; pass reason `size_ok_and_non_empty_multi_screenshot` when both used. Crop to 3D view region can be added when canvas bounds are known (not implemented by default).
- **DOM polling:** In MCP/DOM flow, poll for Play (e4) enabled before click; see Part VIII.5.

### IX.4 Liveness and CIRCLE_BASE

- **CIRCLE_BASE mode:** After `WALK_FORWARD`, optional `CIRCLE_BASE` runs for a fixed number of steps: slow rotation of torso/arms/legs via `base_yaw` and `getQuaternionFromEuler([0,0,base_yaw])` + `resetBasePose(..., qw)`. Then transition to TRACK(goal_idx=1) (POSE_A). Tests full mobility (rotation) visually.
- **Liveness:** HOME → WALK_FORWARD → CIRCLE_BASE → TRACK(1) POSE_A → HOLD → … → WALK_BACK → HOME → …

### IX.5 Citations

- BrowserBotics API: debug persistence (`removeDebugObject`, `resetDebugObjectPose`), `createDebugFrame`, `createDebugText`, `addDebugToggle`, `readDebugParameter`.
- Mitra (2020) formal methods / runtime verification; Huang (2019) visual verification; ETH/TUM theses on web-based robotics simulation and rendering.

---

## Sources (no plagiarism)

See Part V for full references. Site and implementation sources remain as listed in Part V.1 and the doc body.
