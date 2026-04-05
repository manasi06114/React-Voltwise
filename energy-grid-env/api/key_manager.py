"""
API Key Rotation Manager
Manages multiple Gemini API keys and automatically rotates between them
when one is exhausted or rate-limited.
"""

import os
import random
from typing import List, Optional


class APIKeyManager:
    """
    Manages multiple API keys and rotates through them when rate limits are hit.
    """
    
    def __init__(self):
        self.api_keys = self._load_api_keys()
        self.failed_keys = set()
        self.current_key_index = 0
        
        if not self.api_keys:
            raise RuntimeError("No Gemini API keys found in environment!")
        
        print(f"✅ Loaded {len(self.api_keys)} API keys")
    
    def _load_api_keys(self) -> List[str]:
        """
        Load all API keys from environment.
        Supports both:
        - GEMINI_API_KEY=key1 (single key, will be overwritten)
        - .env file with multiple GEMINI_API_KEY lines
        """
        api_keys = []
        
        # Try to load from .env file first
        # Path: energy-grid-env/api/key_manager.py -> go up 3 levels to voltwise/
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        env_path = os.path.join(current_dir, ".env")
        
        print(f"🔍 Looking for .env file at: {env_path}")
        
        if os.path.exists(env_path):
            print(f"✅ Found .env file")
            with open(env_path, "r", encoding="utf-8") as f:
                line_count = 0
                for line in f:
                    line_count += 1
                    line = line.strip()
                    print(f"   Line {line_count}: {line[:50] if line else '(empty)'}")
                    if line and line.startswith("GEMINI_API_KEY="):
                        key = line.split("=", 1)[1].strip()
                        if key:
                            api_keys.append(key)
                            print(f"   ✅ Loaded API key #{len(api_keys)}: {key[:20]}...")
        else:
            print(f"❌ .env file not found at {env_path}")
        
        # Fallback to environment variable if no file keys found
        if not api_keys:
            print(f"⚠️  No keys found in file, checking environment variable...")
            single_key = os.environ.get("GEMINI_API_KEY")
            if single_key:
                api_keys.append(single_key)
                print(f"✅ Loaded from environment: {single_key[:20]}...")
        
        return api_keys
    
    def get_key(self) -> str:
        """
        Get an available API key.
        Returns a random key from non-failed keys.
        """
        available_keys = [k for k in self.api_keys if k not in self.failed_keys]
        
        if not available_keys:
            # All keys failed, reset and try again
            print("⚠️  All API keys exhausted! Resetting failed keys list...")
            self.failed_keys.clear()
            available_keys = self.api_keys
        
        if not available_keys:
            raise RuntimeError("No API keys available!")
        
        # Random selection from available keys
        key = random.choice(available_keys)
        self.current_key_index = self.api_keys.index(key)
        return key
    
    def mark_key_failed(self, api_key: str) -> None:
        """
        Mark an API key as failed (quota exceeded or rate limited).
        """
        self.failed_keys.add(api_key)
        failed_count = len(self.failed_keys)
        print(f"⚠️  API Key failed. Failed count: {failed_count}/{len(self.api_keys)}")
        
        if failed_count == len(self.api_keys):
            print("🔄 All keys exhausted. Resetting...")
            self.failed_keys.clear()
    
    def get_status(self) -> dict:
        """Get current key manager status."""
        return {
            "total_keys": len(self.api_keys),
            "failed_keys": len(self.failed_keys),
            "available_keys": len(self.api_keys) - len(self.failed_keys),
            "current_key_index": self.current_key_index,
        }


# Global instance
_key_manager: Optional[APIKeyManager] = None


def get_key_manager() -> APIKeyManager:
    """Get or create the global key manager."""
    global _key_manager
    if _key_manager is None:
        _key_manager = APIKeyManager()
    return _key_manager
