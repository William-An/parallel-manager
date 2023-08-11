from enum import Enum
from asyncio import Queue

class RequestStatus(Enum):
    CREATED = 1
    PENDING = 2
    RUNNING = 3
    FINISHED = 4

class BaseRequestPacket:
    def __init__(self, id: int) -> None:
        self.id = id

class BaseResponsePacket:
    def __init__(self, req: BaseRequestPacket):
        self.req = req

class ShellRequestPacket(BaseRequestPacket):
    def __init__(self, id: int, desc: str, cmd: str) -> None:
        super().__init__(id)
        self.desc = desc
        self.cmd = cmd
        self.status = RequestStatus.CREATED

class ShellResponsePacket(BaseResponsePacket):
    def __init__(self, req: ShellRequestPacket, retcode: int, elapsed_secs: int) -> None:
        super().__init__(req)
        self.retcode = retcode
        self.elapsed_secs = elapsed_secs

# Common Type definitions
# TODO: Asyncio Queue is not typing with generics?
# RequestQueue = Queue[BaseRequestPacket]
# ResponseQueue = Queue[BaseResponsePacket]
RequestQueue = Queue
ResponseQueue = Queue