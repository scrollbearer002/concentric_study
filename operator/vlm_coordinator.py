#!/usr/bin/env python3
"""
VLM Coordinator for CRE Kernel.
Handles Vision-Language Model integration with Set-of-Mark preprocessing.

Academic validation:
- Set-of-Mark (SoM) preprocessing enables standard VLMs to achieve GUI-specialized accuracy
- Microsoft Research: "Set-of-Mark Prompting Unleashes Extraordinary Visual Grounding in GPT-4V"
- Without SoM, standard VLMs suffer from "spatial dilution" (patch-level granularity vs. pixel-level precision)
"""

from __future__ import annotations

import base64
import json
import io
from typing import Any

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = None  # type: ignore
    ImageDraw = None  # type: ignore

try:
    import openai
except ImportError:
    openai = None

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None  # type: ignore
    types = None  # type: ignore

from codex_client import CodexClient


def apply_set_of_mark(screenshot_bytes: bytes, grid_spacing: int = 100) -> bytes:
    """
    Apply Set-of-Mark preprocessing to screenshot.
    
    Academic validation: Overlays grid/marks to help VLM with spatial grounding.
    Microsoft Research proved this enables standard VLMs to match GUI-specialized model accuracy.
    
    Args:
        screenshot_bytes: Raw PNG bytes from screenshot
        grid_spacing: Pixel spacing between grid lines (default 100)
    
    Returns:
        Modified screenshot bytes with grid overlay
    """
    if Image is None or ImageDraw is None:
        raise RuntimeError("PIL (Pillow) required for Set-of-Mark preprocessing: pip install Pillow")
    
    img = Image.open(io.BytesIO(screenshot_bytes))
    draw = ImageDraw.Draw(img)
    
    width, height = img.size
    
    # Draw vertical grid lines with labels
    for x in range(0, width, grid_spacing):
        draw.line([(x, 0), (x, height)], fill=(255, 0, 0), width=1)
        # Label columns
        if x > 0:
            try:
                # Try to use default font, fallback to basic if not available
                font = ImageFont.load_default()
                draw.text((x + 5, 5), str(x), fill=(255, 0, 0), font=font)
            except Exception:
                draw.text((x + 5, 5), str(x), fill=(255, 0, 0))
    
    # Draw horizontal grid lines with labels
    for y in range(0, height, grid_spacing):
        draw.line([(0, y), (width, y)], fill=(255, 0, 0), width=1)
        # Label rows
        if y > 0:
            try:
                font = ImageFont.load_default()
                draw.text((5, y + 5), str(y), fill=(255, 0, 0), font=font)
            except Exception:
                draw.text((5, y + 5), str(y), fill=(255, 0, 0))
    
    # Convert back to bytes
    output = io.BytesIO()
    img.save(output, format='PNG')
    return output.getvalue()


class VLMCoordinator:
    """
    Coordinates VLM vision with CRE kernel execution.
    
    Uses Set-of-Mark preprocessing to enable standard VLMs (GPT-4o) to achieve
    GUI-specialized model accuracy for coordinate prediction.
    """
    
    def __init__(self, client: CodexClient, api_key: str | None = None, model: str = "gemini-2.5-pro"):
        """
        Initialize VLM Coordinator.
        
        Args:
            client: CodexClient instance for kernel communication
            api_key: API key (OpenAI or Google Gemini, or set OPENAI_API_KEY/GEMINI_API_KEY env var)
            model: Model to use ("gpt-4o", "gemini-2.5-pro", "gemini-1.5-pro", etc.)
        """
        self.client = client
        self.model = model
        
        if model.startswith("gpt"):
            if openai is None:
                raise RuntimeError("OpenAI library required: pip install openai")
            self.api_key = api_key or openai.api_key if hasattr(openai, 'api_key') else None
            if not self.api_key:
                import os
                self.api_key = os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                raise RuntimeError("OpenAI API key required. Set OPENAI_API_KEY env var or pass api_key parameter")
            self.openai_client = openai.OpenAI(api_key=self.api_key)
            self.gemini_client = None
        elif model.startswith("gemini"):
            if genai is None:
                raise RuntimeError("Google Gemini library required: pip install google-genai")
            self.api_key = api_key
            if not self.api_key:
                import os
                self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")  # Support both env vars
            if not self.api_key:
                raise RuntimeError("Gemini API key required. Set GEMINI_API_KEY or OPENAI_API_KEY env var or pass api_key parameter")
            self.gemini_client = genai.Client(api_key=self.api_key)
            self.openai_client = None
        else:
            raise NotImplementedError(f"Model {model} not yet implemented")
    
    def find_element(self, screenshot_bytes: bytes, prompt: str, use_som: bool = True) -> dict[str, int]:
        """
        Use VLM to find UI element and return coordinates.
        
        Args:
            screenshot_bytes: Raw PNG bytes from screenshot
            prompt: Description of element to find (e.g., "red color swatch", "draw tool icon")
            use_som: Apply Set-of-Mark preprocessing (recommended for standard VLMs)
        
        Returns:
            Dict with 'x' and 'y' pixel coordinates
        """
        # Apply Set-of-Mark preprocessing if requested
        if use_som:
            screenshot_bytes = apply_set_of_mark(screenshot_bytes)
        
        # Base64 encode screenshot
        screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
        
        # Call VLM API
        if self.model.startswith("gpt"):
            return self._predict_with_gpt4o(screenshot_b64, prompt)
        elif self.model.startswith("gemini"):
            return self._predict_with_gemini(screenshot_bytes, prompt)
        else:
            raise NotImplementedError(f"Model {self.model} not yet implemented")
    
    def _predict_with_gpt4o(self, screenshot_b64: str, prompt: str) -> dict[str, int]:
        """Use GPT-4o Vision API to predict coordinates."""
        response = self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a GUI automation assistant. Analyze the screenshot and return the exact pixel coordinates "
                        "(x, y) of the UI element described. The screenshot has a grid overlay with coordinates labeled. "
                        "Return ONLY a JSON object with 'x' and 'y' keys. Example: {'x': 400, 'y': 200}"
                    )
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
        result_text = response.choices[0].message.content.strip()
        
        # Extract JSON (handle markdown code blocks if present)
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()
        
        coordinates = json.loads(result_text)
        return {'x': int(coordinates['x']), 'y': int(coordinates['y'])}
    
    def _predict_with_gemini(self, screenshot_bytes: bytes, prompt: str) -> dict[str, int]:
        """Use Google Gemini API to predict coordinates."""
        response = self.gemini_client.models.generate_content(
            model=self.model,
            contents=[
                types.Part.from_bytes(data=screenshot_bytes, mime_type='image/png'),
                f"Find the {prompt} and return its center coordinates as JSON: {{'x': <number>, 'y': <number>}}. The screenshot has a grid overlay with coordinates labeled."
            ]
        )
        
        result_text = response.text.strip()
        
        # Extract JSON (handle markdown code blocks if present)
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()
        
        coordinates = json.loads(result_text)
        return {'x': int(coordinates['x']), 'y': int(coordinates['y'])}
    
    def get_next_action(self, screenshot_bytes: bytes, history: list[dict[str, Any]], goal: str = "Draw a red triangle on the Excalidraw canvas", use_som: bool = True) -> str:
        """
        Chain-of-Visual-Thought (CoVT) method: Get next action with reflection.
        
        Academic validation:
        - Enforces closed-loop architecture (Action -> Observation -> Reflection -> Action)
        - Forces VLM to verify previous action before proceeding
        - Implements self-correction mechanism (EvoCUA 2025 research)
        
        Args:
            screenshot_bytes: Raw PNG bytes from current screenshot
            history: List of past actions with their results
            goal: The overall goal the agent is trying to achieve
            use_som: Apply Set-of-Mark preprocessing
        
        Returns:
            JSON string with reflection, action_type, and args
        """
        # Apply Set-of-Mark preprocessing if requested
        if use_som:
            screenshot_bytes = apply_set_of_mark(screenshot_bytes)
        
        # Base64 encode screenshot
        screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
        
        # Build history context
        history_text = ""
        if history:
            history_text = "\n\nPAST ACTIONS:\n"
            for i, action in enumerate(history[-5:], 1):  # Last 5 actions for context
                history_text += f"{i}. {action.get('attempted_action', 'unknown')} with args {action.get('args', {})}\n"
        
        # CoVT System Prompt (enforces reflection before action)
        system_prompt = """You are a self-correcting, visual-first AI agent navigating a macOS interface.
You operate in a strict CLOSED-LOOP (Action -> Observation -> Reflection -> Action).

GOAL: Draw a red triangle on the Excalidraw canvas.
KNOWLEDGE (Agentic RAG): In Excalidraw, pressing the 'p' key selects the Pen tool. Pressing '0' opens the color menu.

For every turn, you will receive the CURRENT SCREENSHOT and a HISTORY of your past actions.

YOUR INSTRUCTIONS:
1. REFLECT: Look at the current screenshot. Did your PREVIOUS action succeed? Provide visual evidence (e.g., "I pressed 'p', and I now see the Pen tool is highlighted purple in the toolbar").
2. CORRECT: If the previous action failed, you must output a new action to retry or fix the error.
3. ACT: If successful, output the next logical action.

AVAILABLE ACTIONS:
- "keystroke": {"key": "<string>"} (Use this to select tools if shortcuts are known)
- "click": {"x": <int>, "y": <int>} (Use this to click color swatches or UI elements)
- "draw_path": {"vertices": [[x1, y1], [x2, y2], [x3, y3], [x1, y1]]} (Use this for the triangle)
- "verify_success": {} (Use this when the goal is complete)

You must output ONLY valid JSON in this exact format:
{
  "reflection": "<Your detailed visual verification of the previous step>",
  "action_type": "<action_name>",
  "args": { <arguments> }
}"""
        
        user_prompt = f"""CURRENT GOAL: {goal}
{history_text}

Analyze the current screenshot and determine your next action.
Remember: Always REFLECT on whether your previous action succeeded before proceeding."""
        
        # Call VLM API
        if self.model.startswith("gpt"):
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": user_prompt
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
                max_tokens=300,
                temperature=0.3  # Lower temperature for more consistent JSON output
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Extract JSON (handle markdown code blocks if present)
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            return result_text
        elif self.model.startswith("gemini"):
            # Gemini API call
            response = self.gemini_client.models.generate_content(
                model=self.model,
                contents=[
                    types.Part.from_bytes(data=screenshot_bytes, mime_type='image/png'),
                    system_prompt + "\n\n" + user_prompt
                ],
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 300,
                }
            )
            
            result_text = response.text.strip()
            
            # Extract JSON (handle markdown code blocks if present)
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            return result_text
        else:
            raise NotImplementedError(f"Model {self.model} not yet implemented")
