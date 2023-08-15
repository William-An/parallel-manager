from parallel_manager.manager import BaseShellManager
from parallel_manager.workerGroup import ShellWorkerGroup, save_failed_shell_request_handler
import logging
import asyncio
import time

async def Main():
    """
    This example shows how to create a shell worker manager,
    submit tasks to them, and wait for the worker to process
    """
    # Initialize workers
    simpleShellWorkergroup = ShellWorkerGroup("simpleShellWorkergroup", "./log", 10, response_handler=save_failed_shell_request_handler)
    simpleShellManager = BaseShellManager("simpleShellManager")
    simpleShellManager.add_workergroup("shell", simpleShellWorkergroup)
    await simpleShellManager.init()

    # Add requests
    for i in range(10):
        print(i)
        simpleShellManager.add_shell_request(f"Failing with code {i}", f"exit {i}")

    # Wait til all requests are done
    await simpleShellManager.done()

logging.basicConfig(level=logging.INFO)
asyncio.run(Main())