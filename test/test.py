from parallel_manager.manager import BaseShellManager
from parallel_manager.workerGroup import ShellWorkerGroup
import logging
import asyncio
import time

async def Main():
    # Initialize workers
    simpleShellWorkergroup = ShellWorkerGroup("simpleShellWorkergroup",
                                        logging.getLogger(),
                                        "./log",
                                        10)
    simpleShellManager = BaseShellManager("simpleShellManager")
    simpleShellManager.add_workergroup("shell", simpleShellWorkergroup)
    await simpleShellManager.init()

    # Add requests
    for i in range(10):
        print(i)
        simpleShellManager.add_shell_request(f"echoing loop-{i}", f"echo {i}")

    # Wait til all requests are done
    await simpleShellManager.done()

asyncio.run(Main())