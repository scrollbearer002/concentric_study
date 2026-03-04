# CRE Kernel - Ultimate Tests

## Test Setup

These tests validate the memory-resident architecture by performing tasks that would fail or look robotic under the old process-bound setup.

**Prerequisites:**
- Kernel running on port 9999
- Screenshot truncation workaround: Use region-based captures for vision
- Smooth mouse movement implemented with Bezier curves

---

## Test 1: Human Simulation - Drawing a Shape

### Objective
Draw a continuous figure-eight or circle in a drawing app to prove smooth, human-like mouse movement.

### What It Proves
- Old `cliclick`: Jagged dots (process spawn per movement)
- New CRE: Smooth continuous line (in-memory Bezier curves)

### Implementation Status
- ✅ `move_mouse` command added to kernel
- ✅ `get_mouse_position` command added to kernel  
- ✅ `smooth_move_and_click()` implemented with Bezier curves
- ⏭️ **Ready to test** - needs drawing app and visual verification

### Test Script
```python
from operator.codex_client import CodexClient
import time

client = CodexClient()

# Open drawing app (Freeform or web canvas)
# Locate canvas center (via screenshot + OCR or coordinates)
canvas_x, canvas_y = 720, 450  # Example coordinates

# Draw figure-eight: two overlapping circles
radius = 100
steps_per_circle = 30

# First circle (top)
for i in range(steps_per_circle):
    angle = (i / steps_per_circle) * 2 * 3.14159
    x = canvas_x + radius * (1 + 0.5 * (1 - abs(angle - 3.14159) / 3.14159))
    y = canvas_y - 50 + radius * (angle / 3.14159 - 1)
    client.move_mouse(int(x), int(y))
    time.sleep(0.01)

# Second circle (bottom) - overlapping
for i in range(steps_per_circle):
    angle = (i / steps_per_circle) * 2 * 3.14159
    x = canvas_x + radius * (1 + 0.5 * (1 - abs(angle - 3.14159) / 3.14159))
    y = canvas_y + 50 - radius * (angle / 3.14159 - 1)
    client.move_mouse(int(x), int(y))
    time.sleep(0.01)
```

**Expected Result:** Smooth, continuous figure-eight without gaps or jumps.

---

## Test 2: Real-Time Reaction - Moving Target

### Objective
Track and click moving targets in a web-based aim trainer or slider puzzle.

### What It Proves
- Old `screencapture`: 294ms disk I/O penalty → too slow for fast targets
- New CRE: In-memory vision → fast enough to track dynamic elements

### Implementation Status
- ✅ Screenshot command working (with region workaround)
- ✅ Click command working
- ⚠️ Full-screen screenshots truncate (use regions for vision)
- ⏭️ **Ready to test** - needs aim trainer URL and coordinate detection

### Test Approach
```python
from operator.codex_client import CodexClient
import time

client = CodexClient()

# Continuously capture small region where target appears
# Detect target position (via OCR or color detection)
# Click target with smooth movement

while True:
    # Capture region (e.g., center 800x600 area)
    img = client.screenshot({'x': 320, 'y': 150, 'w': 800, 'h': 600})
    
    # Process image to find target (OCR, color detection, etc.)
    target_x, target_y = detect_target(img)  # Your detection logic
    
    if target_x and target_y:
        # Smooth move and click
        client.smooth_move_and_click(target_x, target_y, steps=15, duration=0.2)
    
    time.sleep(0.1)  # 10 FPS vision loop
```

**Expected Result:** AI can track and hit targets moving at human-reaction speeds.

---

## Test 3: Visual State Machine - Complex Drag-and-Drop

### Objective
Locate blue icons on Desktop and drag them into Finder window.

### What It Proves
- Tight loop: See → Think → Smooth Move → Click & Hold → Drag → Release → Verify
- No UI freezing (Beachball of Death)
- Seamless vision + input without dropped events

### Implementation Status
- ✅ Screenshot working (region-based)
- ✅ Smooth movement working
- ⏭️ Need drag command (click + hold + move + release)
- ⏭️ **Ready to test** - needs drag implementation

### Required Kernel Command
```lua
-- Drag (click, hold, move, release)
commands.drag = function(args)
  local start_x = tonumber(args.start_x) or 0
  local start_y = tonumber(args.start_y) or 0
  local end_x = tonumber(args.end_x) or 0
  local end_y = tonumber(args.end_y) or 0
  
  -- Move to start, click down, drag, release
  hs.mouse.setAbsolutePosition({x = start_x, y = start_y})
  hs.timer.usleep(50000)  -- 50ms
  hs.eventtap.leftMouseDown(hs.geometry.point(start_x, start_y))
  
  -- Smooth drag
  local steps = 20
  for i = 1, steps do
    local t = i / steps
    local x = start_x + (end_x - start_x) * t
    local y = start_y + (end_y - start_y) * t
    hs.mouse.setAbsolutePosition({x = x, y = y})
    hs.timer.usleep(10000)  -- 10ms per step
  end
  
  hs.eventtap.leftMouseUp(hs.geometry.point(end_x, end_y))
  return { status = "ok" }
end
```

### Test Script
```python
from operator.codex_client import CodexClient

client = CodexClient()

# 1. Capture Desktop region
desktop_img = client.screenshot({'x': 0, 'y': 0, 'w': 1440, 'h': 900})

# 2. Detect blue icons (color detection or OCR)
blue_icons = detect_blue_icons(desktop_img)  # Returns list of (x, y) tuples

# 3. Get Finder window position
finder_state = client.get_ui_tree("Finder")
finder_x, finder_y = get_finder_drop_zone()  # Your logic

# 4. Drag each blue icon to Finder
for icon_x, icon_y in blue_icons:
    client.drag(icon_x, icon_y, finder_x, finder_y)
    time.sleep(0.5)  # Brief pause between drags
```

**Expected Result:** All blue icons smoothly dragged into Finder without UI freezing.

---

## Current Status

### ✅ Implemented
1. Smooth mouse movement with Bezier curves
2. Mouse position tracking
3. Region-based screenshots (workaround for truncation)
4. Click command

### ⏭️ To Implement
1. Drag command (click + hold + move + release)
2. Full-screen screenshot fix (or accept region-based approach)
3. Test scripts for each scenario

### 🎯 Next Steps
1. Add `drag` command to kernel
2. Create test scripts for each scenario
3. Run tests and document results
4. Optimize screenshot further if needed

---

## Notes

**Screenshot Truncation Workaround:**
- Use region-based captures for vision tasks
- Full-screen screenshots may truncate at ~500KB
- 75% scaling applied (25% of original size)
- Consider JPEG encoding for smaller payloads in future

**Smooth Movement:**
- Bezier curves implemented
- 20 steps default for smooth paths
- Configurable duration (default 0.3s)
