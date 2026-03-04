#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

from PIL import Image

from reference_board import build_polo_bear_panther_reference_board

ROOT = Path(__file__).resolve().parent
FINAL_SCREENSHOT = ROOT / 'jspaint_polo_bear_panther_enhanced_final.png'
FINAL_CANVAS = ROOT / 'jspaint_polo_bear_panther_enhanced_canvas.png'


def _osascript(script: str) -> str:
    result = subprocess.run(
        ['osascript', '-e', script],
        capture_output=True,
        text=True,
        timeout=25,
        check=False,
    )
    return (result.stdout or '').strip()


def _safari_open_jspaint() -> None:
    subprocess.run(['open', '-a', 'Safari', 'https://jspaint.app/'], check=True, timeout=5)
    subprocess.run(['osascript', '-e', 'tell application "Safari" to activate'], check=True)
    time.sleep(3)


def _maximize_safari() -> None:
    script = '''
    tell application "Safari" to activate
    tell application "System Events"
      tell process "Safari"
        try
          click menu item "Fill" of menu "Window" of menu bar 1
        end try
      end tell
    end tell
    '''
    _osascript(script)
    time.sleep(0.8)


def _do_js(js: str) -> str:
    one_line = ' '.join(js.split())
    escaped = one_line.replace('\\', '\\\\').replace('"', '\\"')
    return _osascript(f'tell application "Safari" to do JavaScript "{escaped}" in current tab of front window')


def _canvas_info() -> dict[str, float]:
    js = """
    (function(){
      const c = document.querySelectorAll('canvas')[0];
      if (!c) return '';
      const r = c.getBoundingClientRect();
      return JSON.stringify({
        width: c.width,
        height: c.height,
        left: r.left,
        top: r.top,
        cssWidth: r.width,
        cssHeight: r.height,
        innerWidth: window.innerWidth,
        innerHeight: window.innerHeight,
        dpr: window.devicePixelRatio,
        url: location.href,
        title: document.title
      });
    })();
    """
    out = _do_js(js)
    if not out:
        raise RuntimeError('canvas info missing')
    return json.loads(out)


def _draw_enhanced() -> None:
    js = r'''
    (function(){
      try {
        const c = document.querySelectorAll('canvas')[0];
        if (!c) return JSON.stringify({status: 'error', message: 'no_canvas'});
        const ctx = c.getContext('2d');
        const rect = c.getBoundingClientRect();
        const w = c.width;
        const h = c.height;
        const scaleY = rect.height ? (h / rect.height) : 1;
        const visibleBottom = Math.min(h, Math.max(0, (window.innerHeight - rect.top) * scaleY));
        const safeBottom = Math.max(h * 0.80, visibleBottom - h * 0.025);
        const yoff = Math.max(0, h * 0.995 - safeBottom);
        const Y = (value) => value - yoff;
        const cx = w * 0.50;
        const bearTop = Y(h * 0.18);
        const bodyW = w * 0.26;
        const headR = w * 0.10;
        const line = '#23313f';
        const fur = '#f7f6f1';
        const shadow = '#d9d7cf';
        const black = '#111111';
        const gold = '#c8a44d';
        const red = '#9b1d20';
        const bg = '#d8e6f1';
        const bg2 = '#f6fbff';
        const ground = '#b8c3cb';

        function fillStroke(fill, stroke, lw){
          ctx.fillStyle = fill;
          ctx.strokeStyle = stroke;
          ctx.lineWidth = lw;
          ctx.fill();
          ctx.stroke();
        }
        function oval(x,y,rx,ry){
          ctx.beginPath();
          ctx.ellipse(x,y,rx,ry,0,0,Math.PI*2);
        }
        function poly(points){
          ctx.beginPath();
          ctx.moveTo(points[0][0], points[0][1]);
          for(let i=1;i<points.length;i++) ctx.lineTo(points[i][0], points[i][1]);
          ctx.closePath();
        }
        function strokePath(points,lw,color){
          ctx.beginPath();
          ctx.moveTo(points[0][0], points[0][1]);
          for(let i=1;i<points.length;i++) ctx.lineTo(points[i][0], points[i][1]);
          ctx.lineWidth = lw;
          ctx.strokeStyle = color;
          ctx.stroke();
        }
        function text(txt,x,y,size,color){
          ctx.save();
          ctx.fillStyle = color;
          ctx.font = `bold ${size}px Georgia, serif`;
          ctx.textAlign = 'center';
          ctx.fillText(txt,x,y);
          ctx.restore();
        }

        ctx.clearRect(0,0,w,h);
        const grad = ctx.createLinearGradient(0,0,0,h);
        grad.addColorStop(0,bg2);
        grad.addColorStop(1,bg);
        ctx.fillStyle = grad;
        ctx.fillRect(0,0,w,h);
        ctx.fillStyle = ground;
        ctx.fillRect(0,h*0.84,w,h*0.16);
        ctx.strokeStyle = '#95a4ae';
        ctx.lineWidth = 2;
        ctx.beginPath(); ctx.moveTo(0,h*0.84); ctx.lineTo(w,h*0.84); ctx.stroke();

        oval(cx, Y(h*0.53), bodyW*0.55, h*0.23); fillStroke(fur, line, 3);
        oval(cx, bearTop + headR*1.05, headR*1.02, headR*0.95); fillStroke(fur, line, 3);
        oval(cx-headR*0.62, bearTop + headR*0.35, headR*0.24, headR*0.28); fillStroke(fur, line, 2.5);
        oval(cx+headR*0.62, bearTop + headR*0.35, headR*0.22, headR*0.26); fillStroke(fur, line, 2.5);
        oval(cx, bearTop + headR*1.35, headR*0.52, headR*0.40); fillStroke('#efece4', line, 2.5);
        oval(cx, bearTop + headR*1.53, headR*0.14, headR*0.08); fillStroke(black, black, 1.5);
        strokePath([[cx,bearTop + headR*1.60],[cx,bearTop + headR*1.82]],2.2,line);
        strokePath([[cx-headR*0.22,bearTop + headR*1.87],[cx-headR*0.10,bearTop + headR*1.97],[cx,bearTop + headR*1.92]],2.2,line);
        strokePath([[cx+headR*0.22,bearTop + headR*1.87],[cx+headR*0.10,bearTop + headR*1.97],[cx,bearTop + headR*1.92]],2.2,line);

        oval(cx-headR*0.36, bearTop + headR*1.02, headR*0.26, headR*0.16); fillStroke('#202428', line, 2);
        oval(cx+headR*0.36, bearTop + headR*1.02, headR*0.26, headR*0.16); fillStroke('#202428', line, 2);
        strokePath([[cx-headR*0.08,bearTop + headR*1.02],[cx+headR*0.08,bearTop + headR*1.02]],2,line);

        ctx.beginPath();
        ctx.ellipse(cx-headR*0.10, bearTop - headR*0.28, headR*0.92, headR*0.26, -0.1, Math.PI*0.05, Math.PI*0.95);
        ctx.lineTo(cx-headR*0.82, bearTop - headR*0.14);
        fillStroke('#151515', line, 3);
        poly([[cx+headR*0.12,bearTop-headR*0.24],[cx+headR*0.24,bearTop-headR*0.55],[cx+headR*0.34,bearTop-headR*0.22]]); fillStroke('#151515', line, 2);

        poly([
          [cx-bodyW*0.62, Y(h*0.42)],[cx-bodyW*0.78,Y(h*0.55)],[cx-bodyW*0.72,Y(h*0.72)],[cx-bodyW*0.54,Y(h*0.82)],
          [cx-bodyW*0.18,Y(h*0.84)],[cx,Y(h*0.76)],[cx+bodyW*0.18,Y(h*0.84)],[cx+bodyW*0.54,Y(h*0.82)],
          [cx+bodyW*0.72,Y(h*0.72)],[cx+bodyW*0.78,Y(h*0.55)],[cx+bodyW*0.62,Y(h*0.42)],[cx+bodyW*0.32,Y(h*0.34)],
          [cx-bodyW*0.32,Y(h*0.34)]
        ]); fillStroke('#1b1b1e', line, 3.5);
        strokePath([[cx-bodyW*0.32,Y(h*0.34)],[cx-bodyW*0.10,Y(h*0.55)],[cx-6,Y(h*0.68)]],3,'#5c5c60');
        strokePath([[cx+bodyW*0.32,Y(h*0.34)],[cx+bodyW*0.10,Y(h*0.55)],[cx+6,Y(h*0.68)]],3,'#5c5c60');
        strokePath([[cx,Y(h*0.34)],[cx,Y(h*0.79)]],3,'#6a6a70');
        for (const y of [0.46,0.53,0.60,0.67]) {
          strokePath([[cx-10,Y(h*y)],[cx+10,Y(h*y)]],2,'#8c8c90');
        }
        poly([[cx-bodyW*0.52,Y(h*0.60)],[cx-bodyW*0.28,Y(h*0.56)],[cx-bodyW*0.18,Y(h*0.63)],[cx-bodyW*0.44,Y(h*0.67)]]); fillStroke('#232327','#6a6a70',2);
        poly([[cx+bodyW*0.52,Y(h*0.60)],[cx+bodyW*0.28,Y(h*0.56)],[cx+bodyW*0.18,Y(h*0.63)],[cx+bodyW*0.44,Y(h*0.67)]]); fillStroke('#232327','#6a6a70',2);
        oval(cx+bodyW*0.16, Y(h*0.48), 18, 18); fillStroke(gold, '#7a6224', 2.5);
        text('RL', cx+bodyW*0.16, Y(h*0.49)+7, 16, '#1b1b1e');
        oval(cx-bodyW*0.18, Y(h*0.50), 12, 12); fillStroke(red, '#601214', 2);

        poly([[cx-bodyW*0.58,Y(h*0.44)],[cx-bodyW*0.94,Y(h*0.52)],[cx-bodyW*1.02,Y(h*0.68)],[cx-bodyW*0.88,Y(h*0.79)],[cx-bodyW*0.64,Y(h*0.74)],[cx-bodyW*0.56,Y(h*0.60)]]); fillStroke('#1a1a1d', line, 3);
        poly([[cx+bodyW*0.58,Y(h*0.44)],[cx+bodyW*0.94,Y(h*0.52)],[cx+bodyW*1.02,Y(h*0.68)],[cx+bodyW*0.88,Y(h*0.79)],[cx+bodyW*0.64,Y(h*0.74)],[cx+bodyW*0.56,Y(h*0.60)]]); fillStroke('#1a1a1d', line, 3);
        oval(cx-bodyW*0.88, Y(h*0.80), 16, 11); fillStroke(fur, line, 2.5);
        oval(cx+bodyW*0.88, Y(h*0.80), 16, 11); fillStroke(fur, line, 2.5);

        poly([[cx-bodyW*0.24,Y(h*0.84)],[cx-bodyW*0.30,Y(h*0.96)],[cx-bodyW*0.10,Y(h*0.96)],[cx-bodyW*0.04,Y(h*0.84)]]); fillStroke('#1f2022', line, 3);
        poly([[cx+bodyW*0.24,Y(h*0.84)],[cx+bodyW*0.30,Y(h*0.96)],[cx+bodyW*0.10,Y(h*0.96)],[cx+bodyW*0.04,Y(h*0.84)]]); fillStroke('#1f2022', line, 3);
        poly([[cx-bodyW*0.38,Y(h*0.96)],[cx-bodyW*0.02,Y(h*0.96)],[cx+2,Y(h*0.99)],[cx-bodyW*0.44,Y(h*0.995)]]); fillStroke(black, line, 3);
        poly([[cx+bodyW*0.02,Y(h*0.96)],[cx+bodyW*0.38,Y(h*0.96)],[cx+bodyW*0.44,Y(h*0.995)],[cx-2,Y(h*0.99)]]); fillStroke(black, line, 3);

        ctx.save();
        ctx.globalAlpha = 0.32;
        oval(cx, Y(h*0.60), bodyW*0.33, h*0.10); ctx.fillStyle = shadow; ctx.fill();
        oval(cx, bearTop + headR*1.1, headR*0.82, headR*0.48); ctx.fillStyle = shadow; ctx.fill();
        ctx.restore();
        for (const dx of [-46,-30,-14,14,30,46]) {
          strokePath([[cx+dx,bearTop+headR*0.10],[cx+dx*0.78,bearTop+headR*0.42]],1.6,'#b7b4aa');
        }
        strokePath([[cx-bodyW*0.10,Y(h*0.84)],[cx+bodyW*0.10,Y(h*0.84)]],2.5,'#70737a');

        return JSON.stringify({status: 'ok', width: w, height: h});
      } catch (e) {
        return JSON.stringify({status: 'error', message: String(e)});
      }
    })();
    '''
    out = _do_js(js)
    if not out:
        raise RuntimeError('draw js returned empty output')
    payload = json.loads(out)
    if payload.get('status') != 'ok':
        raise RuntimeError(f"draw js failed: {payload}")


def _crop_canvas_from_screenshot(info: dict[str, float]) -> None:
    with Image.open(FINAL_SCREENSHOT) as image:
        dpr = float(info.get('dpr', 1.0) or 1.0)
        inner_w = float(info.get('innerWidth', info['cssWidth']))
        inner_h = float(info.get('innerHeight', info['cssHeight']))

        visible_left = max(float(info['left']), 0.0)
        visible_top = max(float(info['top']), 0.0)
        visible_right = min(float(info['left'] + info['cssWidth']), inner_w)
        visible_bottom = min(float(info['top'] + info['cssHeight']), inner_h)

        left = int(round(visible_left * dpr))
        top = int(round(visible_top * dpr))
        right = int(round(visible_right * dpr))
        bottom = int(round(visible_bottom * dpr))
        cropped = image.crop((left, top, right, bottom))
        cropped.save(FINAL_CANVAS)


def main() -> None:
    board = build_polo_bear_panther_reference_board()
    written = board.save_split_artifacts(ROOT, 'jspaint_polo_bear_panther_enhanced')
    print(f"[jspaint-enhanced] reference_board={written['reference_board']}")
    _safari_open_jspaint()
    _maximize_safari()
    info = _canvas_info()
    print(f"[jspaint-enhanced] url={info['url']}")
    print(f"[jspaint-enhanced] title={info['title']}")
    print(f"[jspaint-enhanced] canvas={info['cssWidth']}x{info['cssHeight']}")
    _draw_enhanced()
    time.sleep(0.8)
    subprocess.run(['screencapture', '-x', str(FINAL_SCREENSHOT)], check=True)
    _crop_canvas_from_screenshot(info)
    print(f"[done] screenshot={FINAL_SCREENSHOT}")
    print(f"[done] canvas={FINAL_CANVAS}")


if __name__ == '__main__':
    main()
