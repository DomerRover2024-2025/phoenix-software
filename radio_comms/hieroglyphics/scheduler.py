#### scheduler to handle OUTGOING MESSAGES to the base station

###################
##### IMPORTS #####
###################

import serial
from message import Message
from collections import deque
from readerWriter import ReaderWriter
from messageQueue import MessageQueue
from concurrentSet import ConcurrentSet
import time

class Scheduler:

    RETRANSMISSION_COUNTER=1
    BUFFER_BOUND=10

    # topics: dict[str (topic name), int (wrr value)]
    # messages: dict[str (topic name), deque[message]]
    def __init__(self, readerWriter : ReaderWriter, topics : dict[str, int]={}):
        self.readerWriter = readerWriter
        self.topics : dict[str, int] = topics
        self.topics['acknowledgment'] = 5
        self.messages : dict[str, deque[Message]] = {topic : deque() for topic in self.topics}
        self.retransmissionQueue : MessageQueue = MessageQueue()
        # self.acknowledgedMessageIDs : ConcurrentSet = ConcurrentSet()

    def set_topics(self, topics) -> None:
        self.topics = topics
        self.messages = {topic : deque() for topic in self.topics}

    # wrr = weighted round robin value
    # aka: how many messages of THIS one to send
    #      for every wrr value of other topics
    def add_topic(self, topic_name, wrr_val) -> None:
        self.topics[topic_name] = wrr_val
        self.messages[topic_name] = deque()

    # add message to a given "topic"
    # I call this a "topic" but it's probably called a "server" for an actual wrr
    def addMessage(self, message: Message, topic : str='all') -> None:
        if topic not in self.messages:
            raise IndexError(f'Scheduler cannot add message to topic "{topic}" as it does not exist')
        self.messages[topic].append(message)

    def addListOfMessages(self, messageList, topic : str='all') -> None:
        if topic not in self.messages:
            raise IndexError(f'Scheduler cannot add list of messages to topic "{topic}" as it does not exist')
        self.messages[topic].extend(messageList)

    def handleAcknowledgment(self, messageID : int):
        # self.acknowledgedMessageIDs.add(messageID)
        self.retransmissionQueue.removeWithID(messageID)

    # def wasMessageAcknowledged(self, message : Message):
    #     return message.msg_id in self.acknowledgedMessageIDs

    # def removeAcknowledgment(self, message : Message):
    #     self.acknowledgedMessageIDs.remove(message.msg_id)

    def sendMessagesFromTopics(self):
        for topic in self.topics: # all the topic names
            c = 0 # packet counter
            while self.messages[topic] and c < self.topics[topic]:
                currentMessage = self.messages[topic].popleft()
                self.readerWriter.writeMessage(currentMessage)
                print(f'sent message of purpose {currentMessage.purpose.name}')

                if currentMessage.purpose != Message.Purpose.ACK:
                    self.retransmissionQueue.append(currentMessage)
                    if len(self.retransmissionQueue) >= Scheduler.BUFFER_BOUND:
                        return

                c += 1
                # except Exception as e:
                #    print(f'--Error: in the scheduler loop: {e}')

    # weighted round robin algorithm?
    # implement with a thread, I think
    def sendMessages(self, messageQueue : MessageQueue):
        print("started up the wrr", self.topics)
        start = time.time()
        while messageQueue.isRunning():
            if len(self.retransmissionQueue) < Scheduler.BUFFER_BOUND:
                self.sendMessagesFromTopics()
            # except Exception as e:
            #   print('Scheduler problem', e)

            # pop a message
            if time.time() - start < 1:
                continue
            start = time.time()
            limit = min(Scheduler.RETRANSMISSION_COUNTER, len(self.retransmissionQueue))
            for _ in range(limit):
                currentMessage = self.retransmissionQueue.pop()
                # if not self.wasMessageAcknowledged(currentMessage):
                self.readerWriter.writeMessage(currentMessage)
                print(f'Message with id {currentMessage.msg_id} was not acknowledged. Requeueing...')
                self.retransmissionQueue.append(currentMessage)

     # except Exception as e:
     #   print('scheduler', e)
        # talkerNode.destroy_node()
        # rclpy.shutdown()
        # arduino.close()

    # print as a string
    def __str__(self) -> str:
        ret_str = ""
        for topic in self.topics:
            ret_str =f'{ret_str}:name={topic},wrr={self.topics[topic]},num_msg={len(self.messages[topic])}'
        return ret_str
