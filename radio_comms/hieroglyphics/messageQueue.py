# Author: Henry Jochaniewicz
# Date Modified: October 8, 2025
from collections import deque
from message import Message
import threading

class MessageQueue:

    def __init__(self):
        self.queue : list[Message] = deque()
        self.running : bool = True
        self.runningLock = threading.Lock()
        self.condition = threading.Condition()

    def append(self, message : Message):
        with self.condition:
            self.queue.append(message)
            self.condition.notify()

    # really only useful for the retransmission queue.
    def removeWithID(self, messageID : int):
        with self.condition:
            index = None
            for i, message in enumerate(self.queue):
                if message.msg_id == messageID:
                    index = i
                    break
            if index is not None:
                del self.queue[index]

    # Blocking pop.
    def pop(self) -> Message:
        with self.condition:
            while len(self) == 0:
                self.condition.wait(timeout=1)
                if not self.isRunning():
                    return None
            return self.queue.popleft()

    def isRunning(self) -> bool:
        isQueueRunning = False
        with self.runningLock:
            isQueueRunning = self.running
        return isQueueRunning

    def shutdown(self) -> None:
        with self.runningLock:
            self.running = False

    def __len__(self):
        length = 0
        with self.condition:
            length = len(self.queue)
        return length
