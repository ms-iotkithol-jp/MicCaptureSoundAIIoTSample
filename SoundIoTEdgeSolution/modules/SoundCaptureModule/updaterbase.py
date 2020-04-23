from abc import ABCMeta, abstractmethod
import asyncio

class FileUpdaterBase(metaclass=ABCMeta):
    @abstractmethod
    async def uploadFile(self, fileName):
        pass