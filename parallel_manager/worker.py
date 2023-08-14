"""
File name:	worker.py
Created:	08/04/2023
Author:	Weili An
Email:	an107@purdue.edu
Version:	1.0 Initial Design Entry
Description:	Worker class to run commands
"""

import logging
from datetime import datetime
from collections import Counter
from typing import List
from abc import abstractmethod
import asyncio
from .packet import ShellRequestPacket, RequestStatus, ShellResponsePacket, BaseRequestPacket
from .packet import RequestQueue, ResponseQueue

class BaseWorker:
    def __init__(self, name: str, logger: logging.Logger, 
                 taskQueue: RequestQueue, 
                 responseQueue: ResponseQueue) -> None:
        self.name = name
        self.logger = logger
        self.create_time = datetime.now()
        self.start_time = None
        self.processed_tasks = 0
        self.processed_tasks_failed = 0
        self.idle = True
        self.taskQueue = taskQueue
        self.responseQueue = responseQueue
        self.current_request = None

        # Whether to suspend worker execution
        self.not_suspend = asyncio.Event()
        self.not_suspend.set()

    @abstractmethod
    async def _work(self, taskQueue: RequestQueue, 
              responseQueue: ResponseQueue):
        pass

    async def init(self):
        self.taskHandle = asyncio.create_task(
        self._work(self.taskQueue, self.responseQueue), name=self.name)

    async def stop(self):
        """Wrapper function to stop worker
        """
        self.taskHandle.cancel()
        await asyncio.gather(self.taskHandle, return_exceptions=True)

    def suspend(self):
        self.not_suspend.clear()

    def is_suspended(self):
        return not self.not_suspend.is_set()

    def unsuspend(self):
        self.not_suspend.set()

    def get_current_task(self) -> BaseRequestPacket:
        return self.current_request

    async def done(self):
        """Worker is done when all tasks were
        processed
        """
        await self.taskQueue.join()

# TODO Add timeout?
class ShellWorker(BaseWorker):
    """Shell command worker class
    """
    def __init__(self, name: str, logger: logging.Logger, 
                 log_folder: str, taskQueue: RequestQueue, 
                 responseQueue: ResponseQueue) -> None:
        super().__init__(name, logger, taskQueue, responseQueue)
        self.log_folder = log_folder

    async def _work(self, taskQueue: RequestQueue, 
                    responseQueue: ResponseQueue):
        """internal function for processing request from queue


        Args:
            taskQueue (RequestQueue): shell command request queue, first item is request description and second one is the shell command
            responseQueue (ResponseQueue): response queue, worker should send respond to here
        """
        # Worker 
        while True:
            # Test whether worker need to be suspended
            await self.not_suspend.wait()

            # Get cmd description and cmd to launch
            request = await taskQueue.get()
            self.current_request = request
            desc = request.desc
            cmd = request.cmd
            self.idle = False

            # Log start
            self.logger.info(f"[-] job started for {desc}")

            # Create log file for the cmds
            logout = open(f"{self.log_folder}/{desc}.out", "w")
            logerr = open(f"{self.log_folder}/{desc}.err", "w")
            logout.write(f"job description: {desc}\nrun cmd: {cmd}\n")
            logout.write("=" * 80)
            logout.write("\n")
            logout.flush()

            # Launch in subprocess
            start_time = datetime.now()
            proc = await asyncio.create_subprocess_shell(cmd, stdout=logout.fileno(), stderr=logerr.fileno())
            request.status = RequestStatus.RUNNING

            # Log command
            self.logger.info(f"[-] job launched for {desc} with pid {proc.pid}")

            # Waiting for cmd to finish
            retcode = await proc.wait()
            end_time = datetime.now()

            # Compute command run elapsed time
            elapsed_time = end_time - start_time

            if retcode == 0:
                self.logger.info(f"[+] job process finished successfully for {desc}")
            else:
                self.processed_tasks_failed += 1
                self.logger.error(
                    f"[!] job process exited unexpectedly for {desc} with retcode {retcode}")
            
            self.processed_tasks += 1

            request.status = RequestStatus.FINISHED

            # Close files
            logout.close()
            logerr.close()

            # Notify taskQueue we are done
            taskQueue.task_done()

            # Create response packet
            response = ShellResponsePacket(request, retcode, elapsed_time.seconds)

            # Send to response queue
            await responseQueue.put(response)

            # Log done
            self.logger.info(f"[+] job done for {desc}")
            self.idle = True

# Types
WorkerList = List[BaseWorker]