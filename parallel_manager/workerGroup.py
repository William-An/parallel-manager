"""
File name:	workerGroup.py
Created:	08/04/2023
Author:	Weili An
Email:	an107@purdue.edu
Version:	1.0 Initial Design Entry
Description:	Worker group to manage request handling and worker management
"""

from __future__ import annotations
from abc import abstractmethod
from .worker import BaseWorker, ShellWorker
from .worker import WorkerList
from typing import List, Callable
from .packet import BaseRequestPacket, RequestStatus, BaseResponsePacket
from .packet import RequestQueue, ResponseQueue
import asyncio
import logging


# Response handler function type and default
async def _default_response_handler(workgroup: BaseWorkerGroup,
                              responseQueue: ResponseQueue):
    """Default response handler coroutine

    Args:
        workgroup (BaseWorkerGroup): WorkGroup which use this handler
        responseQueue (ResponseQueue): Response queue from Worker
    """

    # Default handler does nothing
    while True:
        await responseQueue.get()
        responseQueue.task_done()

class BaseWorkerGroup:
    def __init__(self, name: str, logger: logging.Logger, 
                 num_workers: int, max_requests: int=-1, 
                 response_handler: ResponseHandlerFn=_default_response_handler) -> None:
        self.workers: WorkerList = []
        self.name = name
        self.logger = logger
        self.num_workers = num_workers
        self.max_requests = max_requests

        # Record response handler function
        self.resHandler = response_handler

    async def init(self):
        # Get the running event loop
        # which is also the loop where queues live
        # so we can safely put items into it in sync code
        self.loop = asyncio.get_running_loop()

        # Create task and response queue
        self.taskQueue = asyncio.Queue(self.max_requests)
        self.responseQueue = asyncio.Queue(self.max_requests)

        # Create response handler
        self.resHandlerTask = asyncio.create_task(self.resHandler(self, self.responseQueue), name=f"{self.name}-responseHandler")

        # Create initial workers
        await self.increment_workers(self.num_workers)

    @abstractmethod
    def get_worker(self, name: str) -> BaseWorker:
        """Create a worker instance corresponding to this workergroup

        Args:
            name (str): worker name

        Returns:
            BaseWorker: worker instance
        """
        pass

    async def done(self):
        await asyncio.gather(*[worker.done() for worker in self.workers])

    async def increment_workers(self, num: int):
        num_existing_workers = len(self.workers)
        for i in range(num):
            worker = self.get_worker(f"worker-{i + num_existing_workers}")
            self.workers.append(worker)
            await worker.init()
            
    def decrement_workers(self, num: int):
        # Remove from end of worker list
        num_existing_workers = len(self.workers)
        if num > num_existing_workers:
            num = num_existing_workers

        # To remove worker safely
        # We first need to suspend the worker
        for i in range(num):
            worker = self.workers[-(i + 1)]
            worker.suspend()
        
        # Then wait for it to become idle
        for i in range(num):
            worker = self.workers[-(i + 1)]
            while (not worker.idle) or (not worker.is_suspended()):
                continue

        # Finally we stop the workers and remove them from
        # the workgroup
        for i in range(num):
            worker = self.workers[-(i + 1)]
            worker.stop()
            self.workers.remove(worker)

    def add_request(self, req: BaseRequestPacket) -> int:
        # Make sure the request was put into the same loop
        # as our queue
        self.loop.call_soon(self.taskQueue.put_nowait, req)

    def total_count(self) -> int:
        return len(self.workers)
    
    def idle_count(self) -> int:
        count = 0
        for worker in self.workers:
            if worker.idle:
                count += 1
        return count
    
    def active_count(self) -> int:
        count = 0
        for worker in self.workers:
            if (not worker.idle and not worker.is_suspended()):
                count += 1
        return count

    def suspend_count(self) -> int:
        count = 0
        for worker in self.workers:
            if worker.is_suspended():
                count += 1
        return count
    
    def pending_tasks_count(self) -> int:
        return self.taskQueue.qsize()
    
    def pending_responses_count(self) -> int:
        return self.responseQueue.qsize()

class ShellWorkerGroup(BaseWorkerGroup):
    def __init__(self, name: str, logger: logging.Logger, log_folder: str, num_workers: int, max_requests: int=-1, response_handler: ResponseHandlerFn=_default_response_handler) -> None:
        super().__init__(name, logger, num_workers, max_requests,
                         response_handler)
        self.log_folder = log_folder

    def get_worker(self, name: str) -> ShellWorker:
        return ShellWorker(f"{self.name}-{name}",
                                       self.logger,
                                       self.log_folder,
                                       self.taskQueue,
                                       self.responseQueue)

# Typing
ResponseHandlerFn = Callable[[BaseWorkerGroup, ResponseQueue], None]
