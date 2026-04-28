import asyncio

class MailQueue:
    def __init__(self, maxsize=400):
        self.queue = asyncio.Queue(maxsize=maxsize)

    async def put(self, item):
        await self.queue.put(item)

    async def get(self):
        return await self.queue.get()

    def size(self):
        return self.queue.qsize()

    def task_done(self):
        self.queue.task_done()