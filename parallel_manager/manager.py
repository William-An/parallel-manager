from __future__ import annotations
from .packet import *
from .workerGroup import *
from typing import Dict
import logging

class BaseWorkerGroupCollideError(Exception):
    def __init__(self, manager:BaseManager, workergroup_name:str, 
                    current_workergroup: BaseWorkerGroup,
                    new_workergroup: BaseWorkerGroup) -> None:
        super().__init__()
        self.manager = manager
        self.workergroup_name = workergroup_name
        self.curr_group = current_workergroup
        self.new_group = new_workergroup
    
    def __str__(self) -> str:
        return f"Manager {self.manager.name}: Worker group name [{self.workergroup_name}] collides. Old group: '{self.curr_group.name}' New group: '{self.new_group.name}'"

class BaseManager:
    """Base workergroup manager
    """
    def __init__(self, name: str) -> None:
        self.workgroups: Dict[str, BaseWorkerGroup] = dict()
        self.name = name
        self.default_name = ""

        # Register callback to save pending tasks
        atexit.register(self.save_pending)

        # TODO Create a async event loop to handle request

    async def init(self):
        for _, group in self.workgroups.items():
            await group.init()

        
    async def done(self):
        await asyncio.gather(*[group.done() for _, group in self.workgroups.items()])

    def add_workergroup(self, name:str, workgroup: BaseWorkerGroup, force=False):
        """Add a workergroup to manager, also set default worker group to 
           the newly added.

        Args:
            name (str): Worker group name
            workgroup (BaseWorkerGroup): Worker group to be added
            force (bool, optional): Whether to update group. Defaults to False. If set to False and the name already exists, an error will be raised

        Raises:
            BaseWorkerGroupCollideError: collided worker groups information
        """
        if force:
            self.workgroups[name] = workgroup
        else:
            if self.workgroups.get(name):
                raise BaseWorkerGroupCollideError(self, name, self.workgroups[name], workgroup)
            else:
                self.workgroups[name] = workgroup

        self.default_name = name

    def add_request(self, req: BaseRequestPacket, workgroup_name: str="Default"):
        if workgroup_name.lower() == "default":
            self.workgroups[self.default_name].add_request(req)
        else:
            self.workgroups[workgroup_name].add_request(req)

    def save_pending(self, prefix:str="") -> None:
        prefix = f"{prefix}{self.name}-"
        for wg in self.workgroups.values():
            wg.save_pending(prefix)

    def load_tasks(self, prefix:str="") -> None:
        prefix = f"{prefix}{self.name}-"
        for wg in self.workgroups.values():
            wg.load_tasks(prefix)

class BaseShellManager(BaseManager):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.next_req_id = 0

    def add_shell_request(self, description:str, cmd:str):
        request = ShellRequestPacket(self.next_req_id, description, cmd)
        self.add_request(request)