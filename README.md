# parallel_manager

[![Python test](https://github.com/William-An/parallel-manager/actions/workflows/python-package.yml/badge.svg)](https://github.com/William-An/parallel-manager/actions/workflows/python-package.yml) [![PyPI version](https://badge.fury.io/py/parallel-manager.svg)](https://badge.fury.io/py/parallel-manager)

A simple shell command manager. Used for running parallel simulations.

## How-to

First install the package with `pip`:

```bash
pip install parallel_manager
```

To run the manager, we will need to wrap the manager initialization and request creations all in a async function like this:

```python
from parallel_manager.manager import BaseShellManager
from parallel_manager.workerGroup import ShellWorkerGroup
import logging
import asyncio

async def Main():
    # Init the manager
    simpleShellWorkergroup = ShellWorkerGroup("simpleShellWorkergroup",
                                        logging.getLogger(),
                                        "./log",
                                        10)
    simpleShellManager = BaseShellManager("simpleShellManager")
    simpleShellManager.add_workergroup("shell", simpleShellWorkergroup)
    await simpleShellManager.init()

    # Adding tasks
    # Here we just run 100 echo
    for i in range(100):
        simpleShellManager.add_shell_request(f"echoing loop-{i}", f"echo {i}")

   # Wait for the manager to finish
   await simpleShellManager.done()
```

Then we simply use `asyncio.run()` to run the above function:

```python
asyncio.run(Main())
```

The manager will run at most `10` processes at a given time and will terminate when all `100` requests are done.

Full example is at [here](./examples/example_simpleShell.py)

## Structure

1. Worker
   1. Receive request from queue and process it
2. WorkerGroup
   1. Manage workers of same class
   2. Collect basic stats from workers
3. Manager
   1. Might host various workergroups with different worker type
   2. Support various ways to add tasks
   3. Control workergroups/workers
   4. Various middleware/plugin to the BaseManager to implement other features like http web monitoring and task submission

## TODOs

### Short-term todos

1. [ ] Manager statistics plugin
2. [ ] Manager summary when all tasks are done
3. [ ] Timeout support
4. [ ] Status monitor, progress monitor
5. [ ] Dump failed task/able to rerun
6. [x] Dump unfinished tasks when script terminates

### Long-term todos

1. [ ] Thread-mode support (completely non-blocking)
   1. [ ] Use a separate thread to run the workers
   2. [ ] Allow to submit task at any time
2. [ ] Http monitor
3. [ ] Interactive control for status monitoring and changing configuration dynamically, treat worker as a server that can submit task to, like a local slurm control
4. [ ] `PythonFunctionWorker` class (execute python function calls) and other worker class as well
5. [ ] Standardize plugin format for each class
   1. [ ] For instance, http server monitor could be a plugin that can be added to any manager class.
