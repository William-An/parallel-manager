from parallel_manager.manager import BaseShellManager
from parallel_manager.workerGroup import ShellWorkerGroup
import logging
import asyncio
import time

async def Main():
    """
    This example shows how to create a shell worker manager,
    submit tasks to them, and wait for the worker to process
    """
    # Initialize workers
    simpleShellWorkergroup = ShellWorkerGroup("simpleShellWorkergroup",
                                        "./log",
                                        10)
    simpleShellManager = BaseShellManager("simpleShellManager")
    simpleShellManager.add_workergroup("shell", simpleShellWorkergroup)
    await simpleShellManager.init()

    # Add requests
    for i in range(20):
        print(i)
        simpleShellManager.add_shell_request(f"sleep for {i} secs", f"sleep {i}")

    # Wait til all requests are done
    await simpleShellManager.done()

logging.basicConfig(level=logging.INFO)
asyncio.run(Main())