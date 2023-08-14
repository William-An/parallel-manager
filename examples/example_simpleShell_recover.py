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
                                        logging.getLogger(),
                                        "./log_resume",
                                        10)
    simpleShellManager = BaseShellManager("simpleShellManager")
    simpleShellManager.add_workergroup("shell", simpleShellWorkergroup)
    await simpleShellManager.init()

    # Load from save file
    simpleShellManager.load_tasks()

    # Resume tasks
    await simpleShellManager.done()
asyncio.run(Main())