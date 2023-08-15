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
from .packet import BaseRequestPacket, ShellRequestPacket, BaseResponsePacket, ShellResponsePacket, RequestStatus
from .packet import RequestQueue, ResponseQueue
from .utils import LogAdapter
from .stats import Statistics
import asyncio
import logging
import os

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

async def save_failed_shell_request_handler(workgroup: ShellWorkerGroup,
                              responseQueue: ResponseQueue):
    filename = f"{workgroup.name}-failed-tasks.save"
    fp = open(filename, "w")
    while True:
        resp: ShellResponsePacket = await responseQueue.get()

        if resp.retcode != 0:
            workgroup.logger.info(f"[-] {workgroup.name}: saving failed request {resp.req.desc}")
            
            # Save failed task
            fp.write(resp.req.serialize())
            fp.write("\n")
            fp.flush()

        responseQueue.task_done()

class BaseWorkerGroup:
    def __init__(self, name: str, num_workers: int, max_requests: int=-1, 
                 response_handler: ResponseHandlerFn=_default_response_handler) -> None:
        self.workers: WorkerList = []
        self.name = name
        self.num_workers = num_workers
        self.max_requests = max_requests
        self.raw_logger = logging.getLogger(__name__)
        self.logger = LogAdapter(self.raw_logger, {"name": name})
        self.logger.debug(f"[-] Creating worker group")

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
        await self.responseQueue.join()

    async def increment_workers(self, num: int):
        num_existing_workers = len(self.workers)
        for i in range(num):
            worker = self.get_worker(f"worker-{i + num_existing_workers}")
            self.workers.append(worker)
            await worker.init()
            
    async def decrement_workers(self, num: int):
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
            await worker.stop()
            self.workers.remove(worker)

    def killall(self):
        """Kill all workers
        """
        for worker in self.workers:
            worker.kill()

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
    
    def save_pending(self, prefix:str="") -> None:
        """Save pending tasks currently in the queue
        """
        filename =  f"{prefix}{self.name}-pending-tasks.save"
        self.logger.info(f"[-] {self.name}: saving pending tasks to {filename}")
        
        # iterate through the tasks queue and dump tasks not in finished state
        with open(filename, "w") as fp:
            # Dump tasks queue
            while not self.taskQueue.empty():
                element:BaseRequestPacket = self.taskQueue.get_nowait()
                fp.write(element.serialize())
                fp.write("\n")

            # Dump not finished tasks in workers
            for worker in self.workers:
                curr_req = worker.get_current_task()
                if curr_req and curr_req.status != RequestStatus.FINISHED:
                    fp.write(curr_req.serialize())
                    fp.write("\n")

    def load_tasks(self, prefix:str="") -> None:
        """Load tasks from file created by `save_pending`

        Args:
            prefix (str): worker group saved tasks filename prefix
        """
        filename =  f"{prefix}{self.name}-pending-tasks.save"
        self.logger.info(f"[-] {self.name}: loading tasks from {filename}")
        
        # Load stuff from file
        with open(filename) as fp:
            for line in fp:
                packet = self.deserialize_task(line)
                self.add_request(packet)

    @abstractmethod
    def deserialize_task(self, string:str) -> BaseRequestPacket:
        """Deserialize a line into worker group specific request packet
        """
        raise NotImplementedError
    
    def get_stats(self) -> Statistics:
        stats = Statistics()
        for worker in self.workers:
            stats += worker.stats

        stats["pending_tasks"] = self.pending_tasks_count()

        return stats

    def summaries(self) -> List[str]:
        """Generate summary text for this worker in lines

        Returns:
            List[str]: lines of text
        """
        return self.summary().splitlines()

    def summary(self) -> str:
        """Generate summary text for this worker in a single string

        Returns:
            str: summary text
        """
        stats = self.get_stats()
        result = f"{self.name}: "
        for name, val in stats.items():
            result = f"{result}\n\t{name}: {val}"

        return result

class ShellWorkerGroup(BaseWorkerGroup):
    def __init__(self, name: str, log_folder: str, num_workers: int, max_requests: int=-1, response_handler: ResponseHandlerFn=_default_response_handler) -> None:
        super().__init__(name, num_workers, max_requests,
                         response_handler)
        self.log_folder = log_folder

        # Create log directory if not existed
        if not os.path.exists(log_folder):
            os.mkdir(log_folder)

    def get_worker(self, name: str) -> ShellWorker:
        return ShellWorker(f"{self.name}-{name}",
                                       self.log_folder,
                                       self.taskQueue,
                                       self.responseQueue)
    
    def deserialize_task(self, string:str) -> ShellRequestPacket:
        tmp = ShellRequestPacket.factory()
        tmp.deserialize(string)
        return tmp

# Typing
ResponseHandlerFn = Callable[[BaseWorkerGroup, ResponseQueue], None]
