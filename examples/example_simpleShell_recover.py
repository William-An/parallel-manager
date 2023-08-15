from parallel_manager.manager import BaseShellManager
from parallel_manager.workerGroup import ShellWorkerGroup
import logging
import asyncio
import time

async def SavePending():
    """
    This function will save pending tasks
    """
    # Initialize workers
    simpleShellWorkergroup = ShellWorkerGroup("simpleShellWorkergroup",
                                        "./log",
                                        10)
    simpleShellManager = BaseShellManager("simpleShellManager")
    simpleShellManager.add_workergroup("shell", simpleShellWorkergroup)
    await simpleShellManager.init()

    # We first add some running tasks
    for i in range(10):
        simpleShellManager.add_shell_request(f"sleeping-for-{i}-secs", f"sleep {i}")

    # Sleep for 5.5 seconds and call save method
    await asyncio.sleep(5.5)
    simpleShellManager.save_pending(prefix=f"./log/")

async def LoadTasks():
    """This function will load saved tasks from file
    """
    simpleShellWorkergroup = ShellWorkerGroup("simpleShellWorkergroup",
                                        "./log",
                                        10)
    simpleShellManager = BaseShellManager("simpleShellManager")
    simpleShellManager.add_workergroup("shell", simpleShellWorkergroup)
    await simpleShellManager.init()

    # Load from save file
    simpleShellManager.load_tasks(prefix=f"./log/")

    # Resume tasks
    await simpleShellManager.done()

logging.basicConfig(level=logging.INFO)
asyncio.run(SavePending())
asyncio.run(LoadTasks())