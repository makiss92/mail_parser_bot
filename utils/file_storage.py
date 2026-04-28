# FILEPATH: utils/file_storage.py

import asyncio
import json
from pathlib import Path

class AsyncJSONStorage:
    def __init__(self, path: str):
        self.path = Path(path)
        self.lock = asyncio.Lock()

    async def read(self):
        async with self.lock:
            if not self.path.exists():
                return []

            return await asyncio.to_thread(self._read_sync)

    def _read_sync(self):
        with open(self.path, "r") as f:
            return json.load(f)

    async def write(self, data):
        async with self.lock:
            await asyncio.to_thread(self._write_sync, data)

    def _write_sync(self, data):
        tmp_path = self.path.with_suffix(".tmp")

        with open(tmp_path, "w") as f:
            json.dump(data, f)

        tmp_path.replace(self.path)

    async def append_unique(self, item):
        data = await self.read()
        if item not in data:
            data.append(item)
            await self.write(data)
