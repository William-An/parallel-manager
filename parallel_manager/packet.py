from enum import Enum
from asyncio import Queue
from abc import abstractmethod
import json

class RequestStatus(Enum):
    CREATED = 1
    PENDING = 2
    RUNNING = 3
    FINISHED = 4

class BaseRequestPacket:
    def __init__(self, id: int) -> None:
        self.id = id
        self.status = RequestStatus.CREATED

    @abstractmethod
    def serialize(self) -> str:
        """Dump packet as string that it can recover later

        Returns:
            str: packet string
        """
        raise NotImplemented()
    
    @abstractmethod
    def deserialize(self, string:str):
        """Create packet from string

        Args:
            string (str): _description_

        Raises:
            NotImplemented: _description_
        """
        raise NotImplemented()
    
    @classmethod
    def factory(cls):
        return cls(0)

    def __str__(self) -> str:
        return self.serialize()

class BaseResponsePacket:
    def __init__(self, req: BaseRequestPacket):
        self.req = req

class ShellRequestPacket(BaseRequestPacket):
    def __init__(self, id: int, desc: str, cmd: str) -> None:
        super().__init__(id)
        self.desc = desc
        self.cmd = cmd
        self.status = RequestStatus.CREATED

    def serialize(self) -> str:
        tmp = dict()
        tmp["id"] = self.id
        tmp["desc"] = self.desc
        tmp["cmd"] = self.cmd
        return json.dumps(tmp)

    def deserialize(self, string:str):
        tmp:dict = json.loads(string)
        for key in tmp.keys():
            if hasattr(self, key):
                setattr(self, key, tmp[key])
        self.status = RequestStatus.CREATED

    @classmethod
    def factory(cls):
        return cls(0, "factory", "echo 0")

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