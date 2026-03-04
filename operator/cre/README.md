# Codex Runtime (CRE) kernel

Hammerspoon HTTP kernel on port 9999. Copy `codex_kernel.lua` to `~/.hammerspoon/init.lua` or require it from your existing init.

## Demo for colleagues

Run the **showcase** (liveness, latency, screenshot, state, full suite hint):

```bash
bash operator/cre/showcase.sh
```

One-pager explaining what CRE does and what it replaces: [SHOWCASE.md](SHOWCASE.md).

## Verify kernel (without `hs -c`)

After reloading Hammerspoon:

```bash
curl -s http://127.0.0.1:9999
curl -s -X POST http://127.0.0.1:9999 -H "Content-Type: application/json" -d '{"command":"ping"}'
```

**Ultimate HTTP-first test** (proves memory-resident AX access, no `hs` CLI):

```bash
curl -v -X POST http://127.0.0.1:9999 \
     -H "Content-Type: application/json" \
     -d '{"command": "dump_state", "args": {"app": "Finder"}}'
```

Expect `HTTP/1.1 200 OK` and JSON like `{"status":"ok","title":"Finder","window":"..."}`. This confirms: port bound before IPC, kernel queried Accessibility API in memory, no `hs` binary used, JSON over socket.

Or run the script:

```bash
bash operator/cre/verify_kernel.sh
```

Full CRE suite:

```bash
bash operator/tests/run_cre_tests.sh
```

## Optional: fix `hs` CLI when cliInstall returns false

If you need `hs -A` or `hs -c` (e.g. for observe_run, window_orchestrator), run once in the Hammerspoon Console:

1. `hs.ipc.cliUninstall(nil, true)`
2. `hs.ipc.cliInstall(nil, true)`

If it still returns false, fix permissions for `/usr/local/bin` and `/usr/local/share/man/man1` (see Hammerspoon docs). CRE tests that use only `curl` to 9999 do not depend on the CLI.
