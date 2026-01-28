
import time
import asyncio
from typing import Optional

class RateLimiter:
    def __init__(self, rate_limit: int = 30, window_seconds: int = 60):
        self.rate_limit = rate_limit
        self.window_seconds = window_seconds
        self.tokens = rate_limit
        self.last_refill = time.time()
        self.lock = asyncio.Lock()
        
    async def acquire(self):
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_refill
            
            # Refill logic (linear refill)
            new_tokens = elapsed * (self.rate_limit / self.window_seconds)
            if new_tokens > 0:
                self.tokens = min(self.rate_limit, self.tokens + new_tokens)
                self.last_refill = now
                
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            else:
                # Calculate wait time
                wait_time = (1 - self.tokens) * (self.window_seconds / self.rate_limit)
                await asyncio.sleep(wait_time)
                self.tokens = 0 # After waiting, we consume the token
                self.last_refill = time.time()
                return True
