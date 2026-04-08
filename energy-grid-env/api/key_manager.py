"""
API Key Rotation Manager
Loads Gemini API keys from a single .env file and rotates through them
when one is exhausted or rate-limited.
"""

import os
import random
from typing import List, Optional
from dotenv import load_dotenv


class APIKeyManager:
    """Manages multiple API keys with automatic rotation on failure."""

    def __init__(self):
        # Load .env from project root
        env_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"
        )
        load_dotenv(env_path)

        self.api_keys = self._load_keys()
        self.failed_keys: set = set()
        self.current_key_index = 0

        if not self.api_keys:
            raise RuntimeError("No API keys found. Set GEMINI_API_KEYS in .env")

        print(f"[KeyManager] Loaded {len(self.api_keys)} API keys")

    @staticmethod
    def _load_keys() -> List[str]:
        """Load keys from GEMINI_API_KEYS (comma-separated) env var."""
        raw = os.environ.get("GEMINI_API_KEYS", "")
        keys = [k.strip() for k in raw.split(",") if k.strip()]

        # Fallback: single key
        if not keys:
            single = os.environ.get("GEMINI_API_KEY", "")
            if single.strip():
                keys = [single.strip()]

        return keys

    def get_key(self) -> str:
        """Get a random available (non-failed) key."""
        available = [k for k in self.api_keys if k not in self.failed_keys]
        if not available:
            self.failed_keys.clear()
            available = self.api_keys
        if not available:
            raise RuntimeError("No API keys available")
        key = random.choice(available)
        self.current_key_index = self.api_keys.index(key)
        return key

    def mark_key_failed(self, api_key: str) -> None:
        """Mark a key as failed (quota/rate-limited)."""
        self.failed_keys.add(api_key)
        print(f"[KeyManager] Key failed ({len(self.failed_keys)}/{len(self.api_keys)})")
        if len(self.failed_keys) >= len(self.api_keys):
            self.failed_keys.clear()

    def get_status(self) -> dict:
        return {
            "total_keys": len(self.api_keys),
            "failed_keys": len(self.failed_keys),
            "available_keys": len(self.api_keys) - len(self.failed_keys),
            "current_key_index": self.current_key_index,
        }


_key_manager: Optional[APIKeyManager] = None


def get_key_manager() -> APIKeyManager:
    global _key_manager
    if _key_manager is None:
        _key_manager = APIKeyManager()
    return _key_manager
