# CRE Kernel: VLM Integration Plan

## Objective

Integrate Vision-Language Models (VLMs) with the CRE kernel to enable **Zero-API Navigation** - OS-agnostic automation that works purely through visual perception.

---

## Current State

### ✅ Completed Prerequisites

1. **Vision Pipeline Fix:**
   - Raw Base64 transmission (bypasses JSON AST)
   - Zero truncation risk
   - Ready for high-resolution feeds

2. **Cubic Bezier Movement:**
   - Human-like mouse trajectories
   - Natural acceleration/deceleration
   - Bot-detection resistant

3. **Low-Latency Architecture:**
   - Memory-resident operations
   - Non-blocking execution
   - <20ms per action

---

## VLM Integration Architecture

### Target Models

1. **CogAgent (CVPR 2024):**
   - 18B parameters
   - 1120x1120 resolution support
   - GUI operation datasets
   - **Status:** Research model (may require API access)

2. **GPT-4o Vision (OpenAI):**
   - Commercial API available
   - High-resolution image support
   - Coordinate prediction capability
   - **Status:** ✅ Available now

3. **Claude 3.5 Sonnet (Anthropic):**
   - Vision capabilities
   - API available
   - **Status:** ✅ Available now

### Recommended: GPT-4o Vision

**Rationale:**
- ✅ Commercial API (immediate availability)
- ✅ High-resolution support
- ✅ Proven coordinate prediction
- ✅ Cost-effective for automation

---

## Implementation Plan

### Phase 1: High-Resolution Screenshot Support

**Objective:** Enable full-resolution screenshots for VLM feeds

**Changes Required:**

1. **Kernel (`codex_kernel.lua`):**
   ```lua
   -- Remove scaling for VLM screenshots
   commands.screenshot = function(args)
     -- ... existing code ...
     -- Only scale if explicitly requested (for backward compatibility)
     if args.scale and tonumber(args.scale) then
       -- Apply scaling
     end
     -- Otherwise: Full resolution (ready for VLM)
   end
   ```

2. **Client (`codex_client.py`):**
   ```python
   def screenshot_vlm(self, region: dict[str, int] | None = None) -> bytes:
       """
       High-resolution screenshot for VLM feeds.
       No scaling applied (full resolution).
       """
       return self.screenshot(region=region, scale=None)
   ```

**Testing:**
- Capture full 4K Retina screenshot
- Verify no truncation (raw Base64 transmission)
- Measure payload size and transmission time

---

### Phase 2: VLM Coordinate Prediction

**Objective:** Integrate VLM API for coordinate prediction

**Implementation:**

```python
# operator/vlm_coordinator.py
import base64
from typing import Any
from codex_client import CodexClient

class VLMCoordinator:
    """Coordinates VLM vision with CRE kernel execution."""
    
    def __init__(self, client: CodexClient, vlm_api_key: str):
        self.client = client
        self.vlm_api_key = vlm_api_key
    
    def find_and_click(self, prompt: str, region: dict[str, int] | None = None) -> dict[str, Any]:
        """
        Find UI element from prompt and click it.
        
        Args:
            prompt: Natural language description (e.g., "Click the Save button")
            region: Optional region to search (reduces VLM processing time)
        
        Returns:
            Result dict with coordinates and click status
        """
        # 1. Capture screenshot
        screenshot_bytes = self.client.screenshot_vlm(region=region)
        
        # 2. Send to VLM API
        coordinates = self._predict_coordinates(screenshot_bytes, prompt)
        
        # 3. Execute smooth click
        result = self.client.smooth_move_and_click(
            coordinates['x'], 
            coordinates['y'],
            steps=20,
            duration=0.3
        )
        
        return {
            'status': 'ok',
            'coordinates': coordinates,
            'click_result': result
        }
    
    def _predict_coordinates(self, screenshot_bytes: bytes, prompt: str) -> dict[str, int]:
        """
        Use VLM API to predict coordinates from screenshot.
        
        Returns:
            Dict with 'x' and 'y' coordinates
        """
        # Base64 encode screenshot
        screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
        
        # Call VLM API (GPT-4o Vision example)
        import openai
        client = openai.OpenAI(api_key=self.vlm_api_key)
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a GUI automation assistant. Analyze the screenshot and return the exact pixel coordinates (x, y) of the UI element described. Return ONLY a JSON object with 'x' and 'y' keys."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Find the {prompt} and return its center coordinates as JSON: {{'x': <number>, 'y': <number>}}"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{screenshot_b64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=50
        )
        
        # Parse response
        import json
        result_text = response.choices[0].message.content
        coordinates = json.loads(result_text)
        
        return {'x': int(coordinates['x']), 'y': int(coordinates['y'])}
```

---

### Phase 3: End-to-End Automation

**Objective:** Complete automation workflows using VLM

**Example Workflow:**

```python
# operator/automation_example.py
from codex_client import CodexClient
from vlm_coordinator import VLMCoordinator

def automate_save_document():
    """Example: Save a document using VLM navigation."""
    client = CodexClient()
    vlm = VLMCoordinator(client, vlm_api_key="...")
    
    # 1. Find and click "File" menu
    vlm.find_and_click("File menu")
    
    # 2. Find and click "Save" option
    vlm.find_and_click("Save option")
    
    # 3. Verify: Check if save dialog appeared
    screenshot = client.screenshot_vlm()
    # ... verify save dialog ...
```

---

## Performance Optimization

### 1. Region-Based Screenshots

**Strategy:** Only capture relevant regions for VLM processing

**Benefit:**
- Reduces VLM API costs (smaller images)
- Faster processing (less data to analyze)
- Lower latency

**Implementation:**
```python
# Capture only menu bar region
menu_region = {'x': 0, 'y': 0, 'w': 1920, 'h': 50}
vlm.find_and_click("File menu", region=menu_region)
```

### 2. Caching

**Strategy:** Cache VLM predictions for repeated queries

**Benefit:**
- Reduces API calls
- Faster repeated operations
- Cost savings

**Implementation:**
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_coordinate_prediction(screenshot_hash: str, prompt: str):
    # Cache VLM predictions
    pass
```

### 3. Compression

**Strategy:** Use JPEG compression for non-critical regions

**Benefit:**
- Smaller payloads
- Faster transmission
- Lower API costs

**Implementation:**
```python
def screenshot_vlm_compressed(self, region: dict[str, int], quality: int = 85):
    """Compressed screenshot for VLM (JPEG instead of PNG)."""
    # Modify kernel to support JPEG encoding
    pass
```

---

## Testing Plan

### Test 1: High-Resolution Screenshot

**Objective:** Verify full-resolution screenshots work without truncation

**Steps:**
1. Capture full 4K Retina screenshot
2. Verify payload size (<10MB Base64)
3. Verify no truncation errors
4. Measure transmission time

**Success Criteria:**
- ✅ No truncation
- ✅ Transmission time <5 seconds
- ✅ Payload size acceptable for VLM API

### Test 2: VLM Coordinate Prediction

**Objective:** Verify VLM can accurately predict coordinates

**Steps:**
1. Capture screenshot with known UI element
2. Send to VLM API with prompt
3. Verify predicted coordinates match actual element
4. Execute click and verify action

**Success Criteria:**
- ✅ Coordinate accuracy >95%
- ✅ Click executes correct action
- ✅ Latency <3 seconds (screenshot + VLM + click)

### Test 3: End-to-End Workflow

**Objective:** Complete automation workflow using VLM

**Steps:**
1. Open application
2. Use VLM to navigate menu
3. Execute multi-step workflow
4. Verify completion

**Success Criteria:**
- ✅ Workflow completes successfully
- ✅ No manual intervention required
- ✅ Human-like movement (cubic Bezier)

---

## Cost Analysis

### GPT-4o Vision API Pricing (as of 2024)

- **Input:** $2.50 per 1M tokens (images count as tokens)
- **Output:** $10.00 per 1M tokens

### Estimated Costs

**Per Screenshot:**
- 4K Retina screenshot: ~1,000 tokens
- Cost per screenshot: ~$0.0025
- 1,000 screenshots: ~$2.50

**Optimization:**
- Region-based screenshots: 50-80% cost reduction
- Caching: 90%+ cost reduction for repeated queries
- Compression: 30-50% cost reduction

---

## Timeline

### Week 1: High-Resolution Support
- ✅ Implement `screenshot_vlm()` method
- ✅ Test full-resolution captures
- ✅ Verify no truncation

### Week 2: VLM Integration
- ✅ Implement `VLMCoordinator` class
- ✅ Integrate GPT-4o Vision API
- ✅ Test coordinate prediction

### Week 3: End-to-End Testing
- ✅ Complete automation workflows
- ✅ Performance optimization
- ✅ Cost analysis

### Week 4: Production Deployment
- ✅ Documentation
- ✅ Error handling
- ✅ Monitoring

---

## Success Metrics

1. **Accuracy:** >95% coordinate prediction accuracy
2. **Latency:** <3 seconds (screenshot + VLM + click)
3. **Cost:** <$0.01 per automation action
4. **Reliability:** >99% success rate for workflows

---

## Conclusion

The CRE kernel is **ready for VLM integration**:

- ✅ Vision pipeline fixed (no truncation)
- ✅ Cubic Bezier movement (human-like)
- ✅ Low-latency architecture (<20ms per action)

**Next Step:** Implement `VLMCoordinator` and test with GPT-4o Vision API.
