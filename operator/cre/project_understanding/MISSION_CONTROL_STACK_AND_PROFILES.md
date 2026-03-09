# Mission-Control Stack and Profiles

This doc ties together the **profile-based supervisor** (mission_control.py), the **tools** it brings up, and **when** to use each profile. Use it together with `LIVE_SAFARI_STACK_CHECKLIST.md` for live browser/macOS tasks.

## What the stack is for

The mission-control stack is an **operational intelligence layer** for real agent work on your machine:

- **Watch the run** — live telemetry and state in one place  
- **Understand the run** — traces, stations, verification outcomes  
- **Debug the run** — when something fails, jump from station to code  
- **Improve the system** — after a run, see where perception, planning, execution, or verification broke  

Not for tiny one-off requests. For **substantial live tasks** (Safari, Mac navigation, installers, multi-step workflows) where you want the system to become more understandable every time it acts.

## Profiles (what to bring up when)

| Profile        | Command                    | Services started        | Use when |
|----------------|----------------------------|-------------------------|----------|
| **live**       | `mission_control.py up live` | Phoenix, Control Room   | Safari, Mac navigation, app workflows, aim trainers, puzzle sites, any visible agent task. **Default for live browser tasks.** |
| **debug**      | `mission_control.py up debug` | Phoenix, Control Room   | Same as live; use when you explicitly want runtime + drilldown focus. |
| **architecture** | `mission_control.py up architecture` | Control Room, Structurizr | Redesign, subsystem understanding, repo/structure mapping. |
| **full**       | `mission_control.py up full`   | Phoenix, Control Room, Structurizr | When you want both live observability and the architecture atlas. |

- **Live task** → auto bring up **live** (Phoenix + Control Room).  
- **Architecture-heavy or redesign** → also (or instead) use **architecture** or **full**.  
- **Code-path debugging** → use Sourcegraph bridge from inside the Control Room when you need to jump from a station to code.

## What each tool does

| Tool            | Role |
|-----------------|------|
| **Control Room** | Command center. Coordinates runtime, conformance, calibration, Sourcegraph links, Structurizr links, station focus. |
| **Phoenix**     | Live runtime truth / flight recorder. Shows what the agent is actually doing (traces, spans). |
| **Structurizr** | Architecture atlas. Use when you need to step back and see how the system is organized. |
| **D2**          | Live architecture diagrams; embedded in the control room (no separate launch). |
| **Sourcegraph bridge** | Code drilldown from the control room when behavior and code need to be connected fast. |

## How this fits the Live Safari checklist

For any **live Safari / visible browser task**:

1. **Bring up the live profile first**  
   `mission_control.py up live [--open]`  
   That gives you Phoenix + Control Room so the run is observable and the evidence pipeline (and optional capture) can run.

2. **Then** follow the rest of the Live Safari checklist:  
   hide Cursor, activate Safari, evidence gate, coordinate discipline, artifact logging.

So: **Mission Control up = live profile for live tasks.** Evidence and capture depend on the stack being up; the stack also gives you observability for every run.

## Commands quick reference

```bash
# Live browser / Safari / macOS app task (default)
python3 operator/cre/project_understanding/tools/mission_control.py up live --open

# Check health
python3 operator/cre/project_understanding/tools/mission_control.py status
python3 operator/cre/project_understanding/tools/mission_control.py doctor

# Architecture-heavy task
python3 operator/cre/project_understanding/tools/mission_control.py up architecture --open

# Tear down
python3 operator/cre/project_understanding/tools/mission_control.py down --all
```

## Research basis

- One supervisor, many specialized tools (no ad hoc launch scripts).  
- Profiles so the right services start for the task type (live vs architecture vs full).  
- Health-based reuse: supervisor checks existing healthy services before starting new ones.  
- Control Room as shell; Phoenix as runtime truth; Structurizr as atlas; Sourcegraph as drilldown.  

See mission_control.py (DEFAULT_PROFILES, up_profile, satisfy_service) and the PhD research memos on the profile-based mission supervisor. For done vs next per angle (operational, control room, integration, documentation, verification), see **NEXT_MOVES_PHD.md**.
