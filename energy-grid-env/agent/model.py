"""
Grid Agent — OpenAI SDK with Gemini backend

Uses the OpenAI Python SDK pointed at Gemini's OpenAI-compatible endpoint.
This is the standard pattern recommended by Google for Gemini API access.

Install: pip install openai python-dotenv
"""

import os
import re
from openai import OpenAI

ACTION_DESCRIPTIONS = {
    0: "redirect_power       -- Redirect electricity between regions",
    1: "charge_battery       -- Store excess energy in batteries",
    2: "discharge_battery    -- Release stored energy from batteries",
    3: "activate_generator   -- Activate fossil fuel backup generator (last resort)",
    4: "curtail_renewable    -- Curtail excess renewable generation to prevent waste",
    5: "redistribute_power   -- Redistribute power evenly across all regions",
}

SYSTEM_PROMPT = """You are an AI controller for a smart electricity grid in Pune, India.
Your goal is to:
  - Satisfy electricity demand at all times (avoid blackouts)
  - Maximise renewable energy usage (solar + wind)
  - Keep battery storage healthy (30%-80%)
  - Avoid activating fossil fuel generators unless critical
  - Avoid wasting excess energy

You will receive the current grid state and must choose exactly ONE action.
Respond with ONLY the action number (0-5) on the first line, followed by a
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

Choose the best action number (0-5):"""


class GeminiGridAgent:
    """
    Smart grid agent using OpenAI SDK with Gemini's OpenAI-compatible endpoint.
    """

    def __init__(self, api_key: str | None = None):
        self._client = OpenAI(
            api_key=api_key or os.environ.get("GEMINI_API_KEY", ""),
            base_url=os.environ.get(
                "GEMINI_BASE_URL",
                "https://generativelanguage.googleapis.com/v1beta/openai/",
            ),
        )
        self._model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")

    def predict(self, obs: dict, verbose: bool = False) -> int:
        """
        Given a grid observation dict, return an action integer (0-5).
        Raises ApiKeyError if the API key is exhausted.
        """
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": _build_prompt(obs)},
                ],
                max_tokens=100,
                temperature=0.3,
            )

            text = response.choices[0].message.content or ""
            if verbose:
                print(text)

            return self._parse_action(text)

        except Exception as e:
            error_msg = str(e).lower()
            if any(kw in error_msg for kw in ['quota', 'rate', 'exhausted', '429', '403', 'permission']):
                raise ApiKeyError(str(e)) from e
            raise

    @staticmethod
    def _parse_action(response: str) -> int:
        """Extract the first digit 0-5 from the response."""
        match = re.search(r"\b([0-5])\b", response)
        if match:
            return int(match.group(1))
        return 5  # fallback: redistribute power


class ApiKeyError(Exception):
    """Raised when an API key is exhausted or rate-limited."""
    pass
