"""API Key rotation manager for handling multiple API keys efficiently."""
from typing import List


class APIKeyManager:
    """Manages API key rotation with round-robin strategy."""
    
    def __init__(self, api_keys: List[str], max_calls_per_key: int = 15):
        """
        Initialize API key manager.
        
        Args:
            api_keys: List of API keys to rotate through
            max_calls_per_key: Maximum calls per key before rotation
        """
        if not api_keys:
            raise ValueError("At least one API key must be provided")
        
        self.api_keys = api_keys
        self.max_calls_per_key = max_calls_per_key
        self.current_index = 0
        self.call_count = 0
        self.total_calls = 0
        
        # Print initialization info
        print(f"\n{'='*70}")
        print(f"🔑 API KEY MANAGER INITIALIZED")
        print(f"{'='*70}")
        print(f"📊 Total API keys loaded: {len(self.api_keys)}")
        print(f"⚙️  Max calls per key: {self.max_calls_per_key}")
        print(f"🎯 Starting with API key #1")
        print(f"{'='*70}\n")
    
    def get_current_key(self) -> str:
        """Get the current active API key."""
        return self.api_keys[self.current_index]
    
    def get_current_key_number(self) -> int:
        """Get current API key number (1-indexed)."""
        return self.current_index + 1
    
    def increment_call_count(self) -> None:
        """Increment call count and rotate if limit reached."""
        self.call_count += 1
        self.total_calls += 1
        
        if self.call_count >= self.max_calls_per_key:
            self._rotate()
    
    def _rotate(self) -> None:
        """Rotate to next API key."""
        old_index = self.current_index
        self.current_index = (self.current_index + 1) % len(self.api_keys)
        self.call_count = 0
        print(f"   🔄 Rotated from API key #{old_index + 1} to #{self.current_index + 1}")
    
    def rotate_on_failure(self) -> None:
        """Manually rotate to next key on failure."""
        self._rotate()
    
    def get_status(self) -> dict:
        """Get current rotation status."""
        return {
            "current_key_number": self.get_current_key_number(),
            "calls_with_current_key": self.call_count,
            "max_calls_per_key": self.max_calls_per_key,
            "total_calls": self.total_calls,
            "total_keys": len(self.api_keys)
        }

