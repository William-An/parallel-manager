# parallel_manager

[![Python test](https://github.com/William-An/parallel-manager/actions/workflows/python-package.yml/badge.svg)](https://github.com/William-An/parallel-manager/actions/workflows/python-package.yml)

A simple shell command manager. Used for running parallel simulations.

## Structure

Separate coroutine from init methods

1. Worker
   1. Receive request from queue and process it
   2. Could have FunctionWorker or ShellWorker?
2. WorkerGroup
   1. Manage workers of same class
   2. Collect basic stats from workers
3. Manager?
   1. Might host various workergroups with different worker type
   2. Support various ways to add tasks
   3. Also to get current status/monitoring
   4. Control workergroups/workers
   5. Various middleware/plugin to the BaseManager to implement other features like http web monitoring and task submission
   6. Has a dedicated async.Runner to host the event loop in this Manager?
   7. non-blocking mode (make this a subclass of BaseManager)
      1. I would like to init the manager with asyncio.run
      2. then could add request to it in synchronous code
      3. Something like

        ```python
        # Async part
        asyncio.run(simpleShellManager.init(), debug=True)

        # Sync part
        for i in range(10):
        print(i)
        simpleShellManager.add_shell_request(f"echoing loop2-{i}", f"echo {i}")
        ```
      4. Update, this is impossible with single threaded program as when .run() finishes, the loop is closed.
      5. Need two threads for this, one for managing the workers, one to submit
   8. BaseManager
      1. Need to have a event loop attribute
      2. BaseManager will need to be wrapped in a coroutine.

## TODO

1. [ ] Request and Response queue for worker
2. [ ] Request and Response class design

3. [] Dump failed cmd to a file
4. [] Slurm rerun task
5. [] Task complete statistics? Worker timed the run time for each cmd executed and plot it at the end or when killed?
6. [] atexit function, dump remaining tasks currently in the queue
7. [] Progress indicator for each task when logging?
8. [] Interactive control for status monitoring and changing configuration dynamically, treat worker as a server that can submit task to, like a local slurm control
9. [] decouple worker and job pushing
10. [] support launching together in a script or subscribe to the worker server
