#!/usr/bin/env python3
"""Open Safari to Magma and reach a blank canvas (PhD arts / realism workflow).

Proven path (MAGMA_LAST_RUN_RESEARCH.md): magma.com → magma.com/app
(redirects to /my/artworks) → click "New canvas" via JS → click "Landscape drawing"
via JS → canvas loads at magma.com/d/<id>. Run this before magma_draw_bmw_e30.py.

Usage:
  cd operator && ./venv/bin/python cre/magma_open_canvas.py
  # Wait until "Canvas ready" then run: ./venv/bin/python cre/magma_draw_bmw_e30.py
"""
from __future__ import annotations

import subprocess
import time


def _osascript(script: str) -> subprocess.CompletedProcess:
    return subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=15)


def _safari_set_url(url: str) -> None:
    _osascript(
        f'tell application "Safari" to set URL of current tab of front window to "{url}"'
    )


def _safari_do_js(js: str) -> str:
    one_line = " ".join(js.split())
    escaped = one_line.replace("\\", "\\\\").replace('"', '\\"')
    r = _osascript(
        f'tell application "Safari" to do JavaScript "{escaped}" in current tab of front window'
    )
    return (r.stdout or "").strip() if r.returncode == 0 else ""


def _safari_get_url() -> str:
    r = _osascript(
        'tell application "Safari" to get URL of current tab of front window'
    )
    return (r.stdout or "").strip() if r.returncode == 0 else ""


def main() -> None:
    print("=== Magma: Open Safari and reach canvas (realism / PhD arts) ===\n")

    # 1) Activate Safari and open Magma
    print("[1] Opening Safari to www.magma.com...")
    subprocess.run(["open", "-a", "Safari", "https://www.magma.com"], check=True, timeout=5)
    time.sleep(3)
    _safari_set_url("https://www.magma.com")
    time.sleep(2)

    # 2) Go to app (redirects to My artworks)
    print("[2] Navigating to magma.com/app (My artworks)...")
    _safari_set_url("https://magma.com/app")
    time.sleep(4)
    url = _safari_get_url()
    if "/my/artworks" not in url and "magma.com" in url:
        time.sleep(2)
        url = _safari_get_url()
    print(f"    URL: {url}")

    # 3) Click "New canvas" via JS (opens dropdown)
    print("[3] Clicking 'New canvas' (JavaScript)...")
    js_new = "(function(){ var el = Array.from(document.querySelectorAll('button, a, [role=button]')).find(function(e){ return e.innerText && e.innerText.trim().indexOf('New canvas') >= 0; }); if (el) { el.click(); return 'clicked'; } return 'not_found'; })();"
    result = _safari_do_js(js_new)
    print(f"    Result: {result}")
    time.sleep(1.5)

    # 4) Click "Landscape drawing" via JS (creates canvas and navigates)
    print("[4] Clicking 'Landscape drawing' (JavaScript)...")
    js_landscape = "(function(){ var el = Array.from(document.querySelectorAll('button, a, [role=menuitem], div')).find(function(e){ return e.innerText && e.innerText.trim().indexOf('Landscape') >= 0; }); if (el) { el.click(); return 'clicked'; } return 'not_found'; })();"
    result = _safari_do_js(js_landscape)
    print(f"    Result: {result}")
    time.sleep(8)

    url = _safari_get_url()
    if "/d/" in url:
        print(f"\n[OK] Canvas ready: {url}")
        print("     Run: ./venv/bin/python cre/magma_draw_bmw_e30.py")
    else:
        print(f"\n[?] URL is {url}. If canvas did not open, run step 3/4 again or click manually.")


if __name__ == "__main__":
    main()
