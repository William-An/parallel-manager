import pytest
import math
import os
import asyncio
import logging
from parallel_manager.manager import BaseShellManager
from parallel_manager.workerGroup import ShellWorkerGroup

class TestBaseShellManager:

    def _test_output_files_exist(self, outfile_name:str, errfile_name:str):
        # Output file should exist
        assert os.path.exists(outfile_name), f"Output file not exist for {outfile_name}"
        assert os.path.exists(errfile_name), f"Error file not exist for {errfile_name}"

        # Error file should be empty
        assert os.stat(errfile_name).st_size == 0, f"Error file should be empty for {errfile_name}"

        # Output file should be non-empty
        assert os.stat(outfile_name).st_size > 0, f"Output file should not be empty for {outfile_name}"

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

            self._test_output_files_exist(outfile_name, errfile_name)

    async def _test_save_load_setup(self, log_dir: str, num_workers: int=10, max_sleep: int=10, stop_time: float=5.5):
        # Initialize workers
        simpleShellWorkergroup = ShellWorkerGroup("simpleShellWorkergroup",
                                            logging.getLogger(),
                                            log_dir,
                                            num_workers)
        simpleShellManager = BaseShellManager("simpleShellManager")
        simpleShellManager.add_workergroup("shell", simpleShellWorkergroup)
        await simpleShellManager.init()

        # Add sleep requests
        for i in range(max_sleep):
            simpleShellManager.add_shell_request(f"sleeping-for-{i}-secs", f"sleep {i}")

        # Sleep for stop_time seconds and call save method
        await asyncio.sleep(stop_time)
        simpleShellManager.save_pending(prefix=f"{log_dir}/")

    def test_save_pending(self, tmp_path):
        """Test if manager could save work properly

        """
        log_dir = f"{tmp_path}/log"

        # Default to have 10 request sleep from 0 - 9 secs
        # and stop after 5.5 seconds
        # should have 10 - ceil(5.5) = 4 pending
        save_file = f"{log_dir}/simpleShellManager-simpleShellWorkergroup-pending-tasks.save"
        max_sleep = 10
        stop_time = 5.5
        num_pending = max_sleep - math.ceil(stop_time)

        # Run the manager
        asyncio.run(self._test_save_load_setup(log_dir, 10, max_sleep, stop_time))

        with open(save_file) as fp:
            lines = fp.readlines()
            count = len(lines)
            assert count == num_pending, f"Max sleep for {max_sleep} seconds and stop after {stop_time} seconds, should have {num_pending} but got {count} pending"


    def test_load_tasks(self, tmp_path):
        """Test if manager could resume work properly

        """
        log_dir = f"{tmp_path}/log"

        # Default to have 10 request sleep from 0 - 9 secs
        # and stop after 5.5 seconds
        # should have 10 - ceil(5.5) = 4 pending
        save_file = f"{log_dir}/simpleShellManager-simpleShellWorkergroup-pending-tasks.save"
        max_sleep = 10
        stop_time = 5.5
        num_remaining = max_sleep - math.ceil(stop_time)

        # Run the manager
        asyncio.run(self._test_save_load_setup(log_dir, 10, max_sleep, stop_time))
       
        # Resume tasks
        async def _test_load_tasks(log_dir: str, num_workers: int=10):
            # Initialize workers
            simpleShellWorkergroup = ShellWorkerGroup("simpleShellWorkergroup",
                                                logging.getLogger(),
                                                log_dir,
                                                num_workers)
            simpleShellManager = BaseShellManager("simpleShellManager")
            simpleShellManager.add_workergroup("shell", simpleShellWorkergroup)
            await simpleShellManager.init()

            # Load request from save
            simpleShellManager.load_tasks(prefix=f"{log_dir}/")

            # Wait til all requests are done
            await simpleShellManager.done()

        # Run resuming work
        asyncio.run(_test_load_tasks(log_dir))

        # Test that the corresponding out and err files exist for resumed tasks
        for i in range(math.ceil(stop_time), max_sleep):
            output_file_base = f"{log_dir}/sleeping-for-{i}-secs"
            errfile_name = f"{output_file_base}.err"
            outfile_name = f"{output_file_base}.out"

            self._test_output_files_exist(outfile_name, errfile_name)
