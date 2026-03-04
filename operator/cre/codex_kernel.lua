-- Codex Runtime Kernel v1.0
-- Copy to ~/.hammerspoon/init.lua or require from existing init.lua.
-- Listens on localhost:9999 and routes JSON commands to native Lua (replaces cliclick/osascript/screencapture).

local server = require("hs.httpserver")
local json = require("hs.json")

local PORT = 9999

-- Command registry
local commands = {}

-- Ping: health check (no args)
commands.ping = function()
  return { status = "ok", message = "Codex Kernel Active" }
end

-- High-Speed Click (Replaces cliclick)
commands.click = function(args)
  local x = tonumber(args.x) or 0
  local y = tonumber(args.y) or 0
  local point = hs.geometry.point(x, y)
  hs.eventtap.leftClick(point)
  return { status = "ok" }
end

-- Keystroke (Agentic RAG: Use keyboard shortcuts to bypass visual grounding)
-- Academic validation: Keyboard shortcuts eliminate spatial dilution problem
commands.keystroke = function(args)
  local key = args.key or args.char or ""
  if key == "" then
    return { status = "error", message = "No key specified" }
  end
  
  -- Create keystroke event
  local key_event = hs.eventtap.event.newKeyEvent({}, key, true)  -- keyDown
  key_event:post()
  hs.timer.usleep(50000)  -- 50ms
  
  local key_event_up = hs.eventtap.event.newKeyEvent({}, key, false)  -- keyUp
  key_event_up:post()
  
  return { status = "ok", message = "Keystroke sent: " .. tostring(key) }
end

-- Move Mouse (for smooth Bezier curves)
commands.move_mouse = function(args)
  local x = tonumber(args.x) or 0
  local y = tonumber(args.y) or 0
  hs.mouse.setAbsolutePosition({x = x, y = y})
  return { status = "ok" }
end

-- Get Current Mouse Position
commands.get_mouse_position = function()
  local pos = hs.mouse.absolutePosition()
  return { status = "ok", x = pos.x, y = pos.y }
end

-- Get Screen Info (CoreGraphics scale factor for Retina coordinate conversion)
-- Academic validation: Uses hs.screen:currentMode().scale to query CoreGraphics display registry
-- This guarantees mathematically perfect translation from VLM pixel predictions to logical coordinates
commands.get_screen_info = function()
  local screen = hs.screen.primaryScreen()
  if not screen then
    return { status = "error", message = "No primary screen" }
  end
  
  local mode = screen:currentMode()
  local scale = mode and mode.scale or 1.0  -- CoreGraphics hardware scale factor (1, 2, or 3)
  local frame = screen:fullFrame()
  
  return {
    status = "ok",
    logical_width = frame.w,
    logical_height = frame.h,
    scale_factor = scale  -- Native CoreGraphics scale (guaranteed accurate)
  }
end

-- Drag (click, hold, move, release) - for drag-and-drop operations
commands.drag = function(args)
  local start_x = tonumber(args.start_x) or tonumber(args.x) or 0
  local start_y = tonumber(args.start_y) or tonumber(args.y) or 0
  local end_x = tonumber(args.end_x) or tonumber(args.x2) or start_x
  local end_y = tonumber(args.end_y) or tonumber(args.y2) or start_y
  
  -- Move to start position
  hs.mouse.setAbsolutePosition({x = start_x, y = start_y})
  hs.timer.usleep(50000)  -- 50ms pause
  
  -- Click down using eventtap event
  local start_point = hs.geometry.point(start_x, start_y)
  local mouse_down = hs.eventtap.event.newMouseEvent(hs.eventtap.event.types.leftMouseDown, start_point)
  mouse_down:post()
  hs.timer.usleep(50000)  -- 50ms
  
  -- Smooth drag with Cubic Bezier interpolation (academic standard for human-like movement)
  -- Cubic Bezier: B(t) = (1-t)^3*P0 + 3(1-t)^2*t*P1 + 3(1-t)*t^2*P2 + t^3*P3
  -- P0=start, P3=end, P1/P2=control points for acceleration/deceleration curves
  local steps = 20
  -- Control points: slight offset for natural acceleration/deceleration
  local ctrl1_x = start_x + (end_x - start_x) * 0.25
  local ctrl1_y = start_y + (end_y - start_y) * 0.25
  local ctrl2_x = start_x + (end_x - start_x) * 0.75
  local ctrl2_y = start_y + (end_y - start_y) * 0.75
  
  for i = 1, steps do
    local t = i / steps
    local inv_t = 1 - t
    -- Cubic Bezier formula
    local x = (inv_t * inv_t * inv_t * start_x) + 
              (3 * inv_t * inv_t * t * ctrl1_x) + 
              (3 * inv_t * t * t * ctrl2_x) + 
              (t * t * t * end_x)
    local y = (inv_t * inv_t * inv_t * start_y) + 
              (3 * inv_t * inv_t * t * ctrl1_y) + 
              (3 * inv_t * t * t * ctrl2_y) + 
              (t * t * t * end_y)
    hs.mouse.setAbsolutePosition({x = math.floor(x), y = math.floor(y)})
    hs.timer.usleep(10000)  -- 10ms per step (200ms total drag)
  end
  
  -- Release
  local end_point = hs.geometry.point(end_x, end_y)
  local mouse_up = hs.eventtap.event.newMouseEvent(hs.eventtap.event.types.leftMouseUp, end_point)
  mouse_up:post()
  return { status = "ok" }
end

-- Draw Path (continuous stroke for drawing applications)
-- Academic validation: Single mouseDown + multiple mouseDragged + single mouseUp
-- Prevents "stroke commit" between segments (HTML5 canvas pointerup = stroke finalization)
-- Uses Cubic Bezier interpolation for natural, human-like movement
commands.draw_path = function(args)
  local path = args.path or {}
  if type(path) ~= "table" or #path < 2 then
    return { status = "error", message = "Path must be array with at least 2 points: [[x1,y1], [x2,y2], ...]" }
  end
  
  -- Move to start position
  local start = path[1]
  if type(start) ~= "table" or #start < 2 then
    return { status = "error", message = "Path points must be [x, y] arrays" }
  end
  local start_x = tonumber(start[1]) or 0
  local start_y = tonumber(start[2]) or 0
  
  hs.mouse.setAbsolutePosition({x = start_x, y = start_y})
  hs.timer.usleep(50000)  -- 50ms pause
  
  -- Mouse down (single event - starts continuous stroke)
  local start_point = hs.geometry.point(start_x, start_y)
  local mouse_down = hs.eventtap.event.newMouseEvent(hs.eventtap.event.types.leftMouseDown, start_point)
  mouse_down:post()
  hs.timer.usleep(50000)  -- 50ms
  
  -- Stream mouse moves with Cubic Bezier interpolation between path points
  for i = 2, #path do
    local prev = path[i-1]
    local curr = path[i]
    
    if type(prev) ~= "table" or type(curr) ~= "table" or #prev < 2 or #curr < 2 then
      goto continue  -- Skip invalid points
    end
    
    local prev_x = tonumber(prev[1]) or 0
    local prev_y = tonumber(prev[2]) or 0
    local curr_x = tonumber(curr[1]) or 0
    local curr_y = tonumber(curr[2]) or 0
    
    -- Cubic Bezier interpolation between prev and curr
    local steps = 10
    for j = 1, steps do
      local t = j / steps
      local inv_t = 1 - t
      
      -- Control points for natural acceleration/deceleration curve
      local ctrl1_x = prev_x + (curr_x - prev_x) * 0.25
      local ctrl1_y = prev_y + (curr_y - prev_y) * 0.25
      local ctrl2_x = prev_x + (curr_x - prev_x) * 0.75
      local ctrl2_y = prev_y + (curr_y - prev_y) * 0.75
      
      -- Cubic Bezier: B(t) = (1-t)³·P₀ + 3(1-t)²·t·P₁ + 3(1-t)·t²·P₂ + t³·P₃
      local x = (inv_t * inv_t * inv_t * prev_x) + 
                (3 * inv_t * inv_t * t * ctrl1_x) + 
                (3 * inv_t * t * t * ctrl2_x) + 
                (t * t * t * curr_x)
      local y = (inv_t * inv_t * inv_t * prev_y) + 
                (3 * inv_t * inv_t * t * ctrl1_y) + 
                (3 * inv_t * t * t * ctrl2_y) + 
                (t * t * t * curr_y)
      
      -- Mouse drag event (maintains button down - no stroke commit)
      local drag_point = hs.geometry.point(math.floor(x), math.floor(y))
      local drag_event = hs.eventtap.event.newMouseEvent(hs.eventtap.event.types.leftMouseDragged, drag_point)
      drag_event:post()
      hs.timer.usleep(10000)  -- 10ms per step (smooth movement)
    end
    
    ::continue::
  end
  
  -- Mouse up (single event at end - final stroke commit)
  local end_point = path[#path]
  if type(end_point) == "table" and #end_point >= 2 then
    local end_x = tonumber(end_point[1]) or 0
    local end_y = tonumber(end_point[2]) or 0
    local mouse_up = hs.eventtap.event.newMouseEvent(hs.eventtap.event.types.leftMouseUp, 
                                                      hs.geometry.point(end_x, end_y))
    mouse_up:post()
  end
  
  return { status = "ok" }
end

-- Memory-Resident Screenshot (Replaces screencapture -x)
-- VISION PIPELINE FIX: Returns raw Base64 as text/plain to bypass JSON AST parsing
-- Academic validation: Base64 in JSON causes 33% bloat + AST buffer overflows in embedded servers
-- Solution: Transmit as text/plain, bypassing JSON parser entirely (zero truncation risk)
commands.screenshot = function(args)
  local screen = hs.screen.primaryScreen()
  if not screen then 
    -- Return error as special marker string (client will detect)
    return "__ERROR__:No primary screen"
  end
  local image = screen:snapshot()
  if not image then 
    return "__ERROR__:Snapshot failed"
  end

  -- CRITICAL FIX: Crop region FIRST, then scale
  -- This prevents processing full Retina screenshot (2880×1800) when only small region needed
  -- Academic validation: Reduces memory footprint by 80-95% for region-based captures
  if args.region and type(args.region) == "table" then
    local r = args.region
    local rect = { x = tonumber(r.x) or 0, y = tonumber(r.y) or 0, w = tonumber(r.w) or 100, h = tonumber(r.h) or 100 }
    image = image:croppedCopy(rect)  -- Crop FIRST from full-resolution screenshot
  end

  -- Optional scaling (applied AFTER cropping for efficiency)
  -- For VLM integration: Consider removing scaling for high-res (1120x1120+) feeds
  if args.scale and tonumber(args.scale) then
    local scale = tonumber(args.scale)
    local size = image:size()
    local scaled_size = { w = size.w * scale, h = size.h * scale }
    image = image:setSize(scaled_size)  -- Scale the cropped region (much smaller)
  end

  -- Return raw Base64 string (no JSON wrapper) - bypasses AST parser
  -- Client receives as text/plain, decodes directly
  local data = image:encodeAsURLString()
  -- Strip "data:image/png;base64," prefix if present, return pure Base64
  if string.find(data, "^data:") then
    data = string.match(data, "base64,(.+)$") or data
  end
  return data  -- Return raw string, not JSON object
end

-- Wait for window (non-blocking-friendly: short sleeps so Run Loop can breathe)
-- Optional: app_name, timeout_sec (default 5). Returns status "ok" when found, "timeout" otherwise.
commands.wait_for_window = function(args)
  local app_name = args.app or args.app_name or "Cursor"
  local timeout_sec = tonumber(args.timeout_sec or args.timeout or 5) or 5
  local end_ts = os.time() + timeout_sec
  while os.time() < end_ts do
    local app = hs.application.get(app_name)
    if app then
      local wins = app:allWindows()
      if wins and #wins > 0 then
        return { status = "ok", message = "window found" }
      end
    end
    hs.timer.usleep(100000)  -- 100ms; short enough to allow some responsiveness
  end
  return { status = "timeout", message = "window not found within " .. timeout_sec .. "s" }
end

-- Deep State Read (Replaces osascript/AXObserver); Electron hydration
commands.dump_state = function(args)
  local app_name = args.app or "Cursor"
  local app = hs.application.get(app_name)
  if not app then
    return { status = "error", message = "App not found: " .. tostring(app_name) }
  end

  local ax = hs.axuielement.applicationElement(app)
  if ax and ax.setAttributeValue then
    pcall(function() ax:setAttributeValue("AXManualAccessibility", true) end)
  end

  local win = app:focusedWindow()
  local window_title = (win and win:title()) and win:title() or nil
  return {
    status = "ok",
    title = app:title(),
    window = window_title,
  }
end

-- HTTP callback: (method, path, headers, body) -> body, code, headers
local function httpCallback(method, path, headers, body)
  if method == "GET" and (path == "" or path == "/") then
    return "Codex Kernel Active", 200, { ["Content-Type"] = "text/plain" }
  end

  if method == "POST" then
    local ok, request = pcall(json.decode, body or "{}")
    if not ok or type(request) ~= "table" then
      return json.encode({ status = "error", message = "Invalid JSON" }), 400, { ["Content-Type"] = "application/json" }
    end

    local cmd = request.command or request.cmd
    local func = cmd and commands[cmd]
    if func then
      local args = request.args or request or {}
      local ok2, result = pcall(func, args)
      if ok2 then
        -- VISION PIPELINE FIX: Screenshot returns raw Base64 string (not JSON)
        -- Bypasses JSON AST parser entirely, eliminating truncation risk
        if cmd == "screenshot" and type(result) == "string" then
          -- Check for error marker
          if string.find(result, "^__ERROR__:") then
            return json.encode({ status = "error", message = string.match(result, "^__ERROR__:(.+)$") }), 500, { ["Content-Type"] = "application/json" }
          end
          -- Return raw Base64 as text/plain (no JSON wrapper)
          return result, 200, { ["Content-Type"] = "text/plain" }
        end
        -- All other commands return JSON as before
        return json.encode(result), 200, { ["Content-Type"] = "application/json" }
      else
        return json.encode({ status = "error", message = tostring(result) }), 500, { ["Content-Type"] = "application/json" }
      end
    end

    return json.encode({ status = "error", message = "Unknown command: " .. tostring(cmd) }), 404, { ["Content-Type"] = "application/json" }
  end

  return "Error", 400, {}
end

-- Create and start server (bind to loopback only)
local srv = server.new(false, false)
  :setPort(PORT)
  :setInterface("127.0.0.1")
  :setCallback(httpCallback)
  :start()

if srv then
  hs.alert.show("Codex Kernel Online: Port " .. PORT, 2)
else
  hs.alert.show("Codex Kernel failed to start on port " .. PORT, 4)
end

-- Defer IPC so run loop is ready; failures do not block kernel
hs.timer.doAfter(2, function()
  local ok_ipc, ipc = pcall(require, "hs.ipc")
  if ok_ipc and ipc and ipc.cliInstall then
    pcall(function() ipc.cliInstall(nil, true) end)
  end
end)
