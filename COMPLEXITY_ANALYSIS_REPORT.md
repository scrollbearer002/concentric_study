# Code Complexity Analysis Report
## Concentric Study Project

**Generated:** February 21, 2026  
**Tool:** Radon (Cyclomatic Complexity Analyzer)  
**Total Lines Analyzed:** 3,554 lines across 12 Python files

---

## 🚨 CRITICAL FINDINGS

### Extremely High Complexity Functions

#### 1. `test_excalidraw_covt.py::run_model_based_agent` 
- **Complexity Score:** **134** (F - Unmaintainable)
- **Location:** Line 450
- **Status:** ⚠️ **CRITICAL REFACTORING REQUIRED**

**Analysis:**
- This is the main test execution function
- Complexity of 134 is **13x higher** than the recommended maximum (10)
- Contains massive nested conditionals and multiple execution paths
- Likely handles: initialization, action execution, verification, error handling all in one function

**Recommendation:**
- **URGENT:** Break this function into smaller, focused functions:
  - `initialize_agent()` - Handle agent setup
  - `execute_action(action)` - Single action execution
  - `verify_action(action)` - Oracle verification
  - `handle_error(error)` - Error handling
  - `generate_evidence()` - Evidence collection
- Consider using a Strategy pattern for different action types
- Extract action handlers into separate classes/functions

---

## ⚠️ HIGH COMPLEXITY FUNCTIONS (Complexity > 10)

### 2. `test_excalidraw_autonomous.py::main`
- **Complexity Score:** **14** (C - High)
- **Location:** Line 179
- **Status:** Needs refactoring

**Recommendation:**
- Break into smaller functions
- Extract test steps into separate methods

### 3. `agent_core.py::MacOSAgentCore.enforce_app_focus`
- **Complexity Score:** **12** (C - High)
- **Location:** Line 134
- **Status:** Needs refactoring

**Recommendation:**
- Simplify focus enforcement logic
- Extract retry logic into separate function

### 4. `vlm_coordinator.py::VLMCoordinator.__init__`
- **Complexity Score:** **12** (C - High)
- **Location:** Line 99
- **Status:** Needs refactoring

**Recommendation:**
- Simplify initialization logic
- Consider using a builder pattern for complex initialization

---

## 📊 MODERATE COMPLEXITY FUNCTIONS (Complexity 6-10)

### Functions Requiring Attention:

1. **`codex_client.py::CodexClient.screenshot`** - Complexity: 10 (B)
   - At the threshold, monitor for growth

2. **`vlm_coordinator.py::VLMCoordinator.get_next_action`** - Complexity: 10 (B)
   - At the threshold, consider simplification

3. **`agent_core.py::MacOSAgentCore.assert_visual_state`** - Complexity: 7 (B)
   - Acceptable but could be simplified

4. **`agent_core.py::MacOSAgentCore.execute_draw_path`** - Complexity: 7 (B)
   - Acceptable complexity for drawing logic

5. **`agent_core.py::MacOSAgentCore.detect_colored_dots`** - Complexity: 6 (B)
   - Acceptable

6. **`agent_core.py::MacOSAgentCore.execute_draw_path_segments`** - Complexity: 6 (B)
   - Acceptable

7. **`test_excalidraw_covt.py::generate_action_plan`** - Complexity: 8 (B)
   - Acceptable but monitor

8. **`test_excalidraw_covt.py::analyze_ui_initial_state`** - Complexity: 7 (B)
   - Acceptable

9. **`vlm_coordinator.py::apply_set_of_mark`** - Complexity: 9 (B)
   - Close to threshold, consider simplification

---

## 📈 MAINTAINABILITY INDEX

### Files with Low Maintainability:

**`cre/test_excalidraw_covt.py`** - **B (Low Maintainability)**
- This is the only file flagged for low maintainability
- Primary cause: `run_model_based_agent` function with complexity 134
- **Action Required:** Immediate refactoring of main function

### Files with Acceptable Maintainability:

All other files have acceptable maintainability scores (A or unmeasured).

---

## 📁 FILE SIZE ANALYSIS

**Total Project Size:** 3,554 lines

**Largest Files:**
- `cre/test_excalidraw_covt.py` - ~1,118 lines (estimated)
- `agent_core.py` - ~638 lines (estimated)
- `vlm_coordinator.py` - ~300+ lines (estimated)
- `codex_client.py` - ~200+ lines (estimated)
- `visual_engine.py` - ~100+ lines (estimated)

**Recommendation:**
- `test_excalidraw_covt.py` is too large - consider splitting into:
  - `test_executor.py` - Test execution logic
  - `action_handlers.py` - Action type handlers
  - `oracle_verification.py` - Oracle/verification logic
  - `evidence_collector.py` - Evidence collection

---

## 🔗 DEPENDENCY ANALYSIS

### Import Relationships:

**`test_excalidraw_covt.py`** imports:
- `agent_core` (MacOSAgentCore)
- `visual_engine` (VisualGroundingEngine)
- `codex_client` (CodexClient)
- `vlm_coordinator` (VLMCoordinator)

**Dependency Graph:**
```
test_excalidraw_covt.py
    ├── agent_core.py
    │   ├── Quartz (external)
    │   ├── Gemini API (external)
    │   └── Pydantic (external)
    ├── visual_engine.py
    │   └── PIL (external)
    ├── codex_client.py
    └── vlm_coordinator.py
        └── codex_client.py
```

**No circular dependencies detected** ✅

---

## 🎯 REFACTORING PRIORITIES

### Priority 1: CRITICAL (Do Immediately)
1. **Refactor `run_model_based_agent`** (Complexity: 134)
   - Break into 5-7 smaller functions
   - Extract action execution logic
   - Separate initialization from execution
   - Extract verification logic

### Priority 2: HIGH (Do Soon)
2. **Refactor `test_excalidraw_autonomous.py::main`** (Complexity: 14)
3. **Refactor `agent_core.py::enforce_app_focus`** (Complexity: 12)
4. **Refactor `vlm_coordinator.py::__init__`** (Complexity: 12)

### Priority 3: MEDIUM (Monitor)
5. **Simplify `codex_client.py::screenshot`** (Complexity: 10)
6. **Simplify `vlm_coordinator.py::get_next_action`** (Complexity: 10)
7. **Consider splitting `test_excalidraw_covt.py`** (1,118 lines)

---

## 💡 REFACTORING STRATEGIES

### For `run_model_based_agent`:

**Current Structure:**
```python
def run_model_based_agent():
    # 600+ lines of nested conditionals
    # Handles: init, execution, verification, errors
```

**Proposed Structure:**
```python
class TestExecutor:
    def __init__(self):
        self.agent = None
        self.vision_engine = None
        # ...
    
    def initialize(self):
        # Extract initialization logic
        pass
    
    def execute_action(self, action):
        # Extract single action execution
        pass
    
    def verify_action(self, action):
        # Extract verification logic
        pass
    
    def run(self):
        # Orchestrate the test
        self.initialize()
        for action in plan:
            self.execute_action(action)
            self.verify_action(action)
```

### For Action Execution:

**Current:** Massive if/elif chain  
**Proposed:** Strategy pattern or dictionary dispatch

```python
ACTION_HANDLERS = {
    "keystroke": handle_keystroke,
    "clear_canvas": handle_clear_canvas,
    "draw_concentric_triangles": handle_draw_triangles,
    # ...
}

def execute_action(action_type, args):
    handler = ACTION_HANDLERS.get(action_type)
    if handler:
        return handler(args)
    else:
        raise ValueError(f"Unknown action: {action_type}")
```

---

## 📊 COMPLEXITY DISTRIBUTION

**By Complexity Grade:**
- **F (51+):** 1 function (run_model_based_agent - 134)
- **C (11-20):** 3 functions
- **B (6-10):** 9 functions
- **A (1-5):** Multiple functions (acceptable)

**Risk Assessment:**
- **Critical Risk:** 1 function (8% of analyzed functions)
- **High Risk:** 3 functions (23% of analyzed functions)
- **Moderate Risk:** 9 functions (69% of analyzed functions)

---

## ✅ POSITIVE FINDINGS

1. **No circular dependencies** detected
2. **Most functions** have acceptable complexity (A-B range)
3. **Core modules** (`agent_core`, `visual_engine`) are relatively clean
4. **Study file** (`study_concentric_logic.py`) has low complexity functions

---

## 🎓 LEARNING OPPORTUNITIES

The high complexity in `run_model_based_agent` is a classic example of:
- **God Object Anti-pattern:** One function doing too much
- **Long Method Smell:** Function too long and complex
- **Feature Envy:** Function accessing too many external objects

**Recommended Reading:**
- "Refactoring" by Martin Fowler
- Strategy Pattern for action handling
- Command Pattern for action execution

---

## 📝 NEXT STEPS

1. **Immediate:** Refactor `run_model_based_agent` into smaller functions
2. **Week 1:** Address Priority 2 refactorings
3. **Week 2:** Split large files, improve structure
4. **Ongoing:** Monitor complexity in new code (keep functions < 10)

---

## 🔄 CONTINUOUS MONITORING

**Recommended Workflow:**
1. Run `radon cc` before committing code
2. Set complexity threshold at 10
3. Refactor functions exceeding threshold
4. Track complexity trends over time

**Command to run:**
```bash
cd operator
./venv/bin/radon cc --min C cre/*.py agent_core.py visual_engine.py
```

---

**Report Generated by:** Radon Complexity Analyzer  
**For Questions:** Review this report and prioritize refactoring based on Priority levels
