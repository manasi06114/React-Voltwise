"""
Gemini Grid Agent
Uses google-genai (gemini-3-flash-preview) with HIGH thinking to decide
which action to take given the current smart grid observation.

Install: pip install google-genai
"""

import os
import re
from google import genai
from google.genai import types

ACTION_DESCRIPTIONS = {
    0: "redirect_power       — Redirect electricity between regions",
    1: "charge_battery       — Store excess energy in batteries",
    2: "discharge_battery    — Release stored energy from batteries",
    3: "activate_generator   — Activate fossil fuel backup generator (last resort)",
    4: "curtail_renewable    — Curtail excess renewable generation to prevent waste",
    5: "redistribute_power   — Redistribute power evenly across all regions",
}

SYSTEM_PROMPT = """You are an AI controller for a smart electricity grid.
Your goal is to:
  - Satisfy electricity demand at all times (avoid blackouts)
  - Maximise renewable energy usage (solar + wind)
  - Keep battery storage healthy (30%–80%)
  - Avoid activating fossil fuel generators unless critical
  - Avoid wasting excess energy

You will receive the current grid state and must choose exactly ONE action.
Respond with ONLY the action number (0–5) on the first line, followed by a
one-sentence reason. Example:
  1
  Charging battery because solar generation exceeds demand.
"""


def _build_prompt(obs: dict) -> str:
    region_lines = "\n".join(
        f"    Region {chr(65+i)}: {d:.1f} MW"
        for i, d in enumerate(obs.get("region_demands", []))
    )
    actions_block = "\n".join(f"  {k}: {v}" for k, v in ACTION_DESCRIPTIONS.items())

    return f"""Current grid state:
  Demand:            {obs['demand']:.1f} MW
  Solar generation:  {obs['solar_generation']:.1f} MW
  Wind generation:   {obs['wind_generation']:.1f} MW
  Battery storage:   {obs['battery_storage']:.1f}%
  Grid capacity:     {obs['grid_capacity']:.1f} MW
  Transmission load: {obs['transmission_load']:.1f}%
  Time of day:       {obs['time_of_day']:02d}:00
  Regional demands:
{region_lines}

Available actions:
{actions_block}

Choose the best action number (0–5):"""


class GeminiGridAgent:
    """
    Smart grid agent powered by Gemini with extended thinking.
    Calls the Gemini API on every step to decide the optimal grid action.
    """

    def __init__(self, api_key: str | None = None):
        self._client = genai.Client(
            api_key=api_key or os.environ.get("GEMINI_API_KEY"),
        )
        self._model = "gemini-2.0-flash"  # Optimized for free tier
        self._config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(
                thinking_level="MEDIUM",  # Reduced from HIGH to save quota
            ),
        )

    def predict(self, obs: dict, verbose: bool = False) -> int:
        """
        Given a grid observation dict, return an action integer (0–5).
        Streams the response and parses the first digit as the action.
        Raises ApiKeyError if the API key is exhausted.
        """
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=SYSTEM_PROMPT + "\n\n" + _build_prompt(obs)),
                ],
            ),
        ]

        try:
            full_response = ""
            for chunk in self._client.models.generate_content_stream(
                model=self._model,
                contents=contents,
                config=self._config,
            ):
                if chunk.text:
                    full_response += chunk.text
                    if verbose:
                        print(chunk.text, end="", flush=True)

            if verbose:
                print()

            return self._parse_action(full_response)
        
        except Exception as e:
            error_msg = str(e).lower()
            # Check for quota/rate limit errors
            if any(keyword in error_msg for keyword in ['quota', 'rate', 'exhausted', '429', '403', 'permission']):
                raise ApiKeyError(str(e)) from e
            else:
                raise


class ApiKeyError(Exception):
    """Raised when an API key is exhausted or rate-limited."""
    pass

    @staticmethod
    def _parse_action(response: str) -> int:
        """Extract the first digit 0–5 from the Gemini response."""
        match = re.search(r"\b([0-5])\b", response)
        if match:
            return int(match.group(1))
        # Fallback: redistribute power (safe default)
        return 5
