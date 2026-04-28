import asyncio
import time

class RateLimiter:
    def __init__(self, rate, per):
        self.rate = rate
        self.per = per
        self.allowance = rate
        self.last_check = time.monotonic()
        self.lock = asyncio.Lock()

    async def acquire(self):
        async with self.lock:
            now = time.monotonic()
            passed = now - self.last_check
            self.last_check = now

            self.allowance += passed * (self.rate / self.per)
            if self.allowance > self.rate:
                self.allowance = self.rate

            if self.allowance < 1:
                sleep_time = (1 - self.allowance) * (self.per / self.rate)
                await asyncio.sleep(sleep_time)
                self.allowance = 0
            else:
                self.allowance -= 1