import pytest
import os
import asyncio
import logging
from parallel_manager.manager import BaseShellManager
from parallel_manager.workerGroup import ShellWorkerGroup

class TestBaseShellManager:

    async def _test_simple_echo_setup(self, log_dir: str, num_workers: int=10):
        # Initialize workers
        simpleShellWorkergroup = ShellWorkerGroup("simpleShellWorkergroup",
                                            logging.getLogger(),
                                            log_dir,
                                            num_workers)
        simpleShellManager = BaseShellManager("simpleShellManager")
        simpleShellManager.add_workergroup("shell", simpleShellWorkergroup)
        await simpleShellManager.init()

        # Add requests
        for i in range(10):
            simpleShellManager.add_shell_request(f"echoing-loop-{i}", f"echo {i}")

        # Wait til all requests are done
        await simpleShellManager.done()

    def test_simple_echo(self, tmp_path):
        # Run the manager
        log_dir = f"{tmp_path}/log"
        asyncio.run(self._test_simple_echo_setup(log_dir, 10))

        # Test for correctness
        for i in range(10):
            output_file_base = f"{log_dir}/echoing-loop-{i}"
            errfile_name = f"{output_file_base}.err"
            outfile_name = f"{output_file_base}.out"

            # Output file should exist
            assert os.path.exists(outfile_name), f"Output file not exist for {outfile_name}"
            assert os.path.exists(errfile_name), f"Error file not exist for {errfile_name}"

            # Error file should be empty
            assert os.stat(errfile_name).st_size == 0, f"Error file should be empty for {errfile_name}"

            # Output file should be non-empty
            assert os.stat(outfile_name).st_size > 0, f"Output file should not be empty for {outfile_name}"


