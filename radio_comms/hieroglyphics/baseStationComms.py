# This is the client side of a client-server model.
# This will be sending requests to the rover.

###################
##### IMPORTS #####
###################

import subprocess
import threading
import traceback
import sys
from serial import Serial

from message import Message
from messageQueue import MessageQueue
import capture_controls
from baseStationMessageProcessor import BaseStationMessageProcessor
from readerWriter import ReaderWriter
from serialReaderWriter import SerialReaderWriter
from socketReaderWriter import SocketReaderWriter
from userInterface import UserInterface
from scheduler import Scheduler
from concurrentSet import ConcurrentSet

#######################
##### GLOBAL VARS #####
#######################

################
##### MAIN #####
################

def main(args):
    if len(args) > 0:
        port = args[0]
    else:
        port = "/dev/cu.usbserial-BG00HO5R"
        # port = "/dev/cu.usbserial-B001VC58"
        # port = "COM4"
        #port = "/dev/ttyUSB0"
    if len(args) > 1:
        host = args[1]
    else:
        host = 'localhost'
    baud = 57600
    timeout = 0.1

    ERR_LOG = "error.log"
    MSG_LOG = "base_station_messages.log"

    # make sure the log file is empty
    open(MSG_LOG, 'w').close()

    messageQueue : MessageQueue = MessageQueue()
    # readerWriter : ReaderWriter = SerialReaderWriter(port, baud, timeout, messageQueue)
    readerWriter : ReaderWriter = SocketReaderWriter(host, 9998, messageQueue, rover=False)

    topics = {
        'all': 1
    } 

    scheduler : Scheduler = Scheduler(readerWriter, topics)
    userInterface : UserInterface = UserInterface(MSG_LOG, scheduler)

    # 3 concurrent threads: one read from serial port, 
    # one for processing messages, one for writing messages
    threads = [
        threading.Thread(target=processMessages, args=(messageQueue, scheduler, ERR_LOG)),
        threading.Thread(target=readMessages, args=(readerWriter, messageQueue)),
        threading.Thread(target=scheduler.sendMessages, args=(messageQueue,)),
    ]

    for t in threads:
        t.start()

    try:
        userInterface.inputLoop()
    except KeyboardInterrupt:
        exit_main(threads, messageQueue)
        exit(0)
    except Exception as e:
        exit_main(threads, messageQueue)
        exit(1)
    exit_main(threads, messageQueue)

#####################
##### FUNCTIONS #####
#####################

def readMessages(readerWriter : ReaderWriter, messageQueue : MessageQueue) -> None:
    while messageQueue.isRunning():
        message = readerWriter.readMessage()
        if message:
            messageQueue.append(message)
            print('message added', len(messageQueue))
    print('exited reading')

def processMessages(messageQueue : MessageQueue, scheduler : Scheduler, ERR_LOG : str) -> None:
    messageProcessor = BaseStationMessageProcessor(ERR_LOG, scheduler)
    alreadyProcessedMessages = ConcurrentSet()
    oldSetOfProcessedMessages = ConcurrentSet()

    while messageQueue.isRunning():
       print('popping message...')
       currentMessage : Message = messageQueue.pop()
       if currentMessage is None:
           return None

       print(f"message popped of purpose {currentMessage.purpose}")

       if currentMessage.purpose == Message.Purpose.ACK:
           messageProcessor.handleAcknowledgment(currentMessage)
           continue

       acknowledgment = messageProcessor.generateAcknowledgment(currentMessage) 
       scheduler.addMessage(acknowledgment, 'acknowledgment')

       # We've already processed this message.
       if currentMessage.msg_id in alreadyProcessedMessages or currentMessage.msg_id in oldSetOfProcessedMessages:
           continue

       alreadyProcessedMessages.add(currentMessage.msg_id)

       if len(alreadyProcessedMessages) >= Scheduler.BUFFER_BOUND:
            oldSetOfProcessedMessages = alreadyProcessedMessages
            alreadyProcessedMessages = ConcurrentSet()


       if currentMessage.purpose == Message.Purpose.ERROR: 
           messageProcessor.handleDebugMessage(currentMessage)

       elif currentMessage.purpose == Message.Purpose.HEARTBEAT: 
           pass

       elif currentMessage.purpose == Message.Purpose.VIDEO:
           messageProcessor.handleVideoMessage(currentMessage)

       elif currentMessage.purpose == Message.Purpose.HIGH_DEFINITION_PHOTO:
           messageProcessor.handleHighDefPhotoMessage(currentMessage)

       elif currentMessage.purpose == Message.Purpose.LOW_DEFINITION_PHOTO:
           messageProcessor.handleLowDefPhotoMessage(currentMessage)

       elif currentMessage.purpose == Message.Purpose.FILE_CONTENTS:
           messageProcessor.readFileOverPort(currentMessage) 

       else:
           print("unknown message purpose")

# everything to do on shutdown
def exit_main(threads : list[threading.Thread], messageQueue : MessageQueue):
    messageQueue.shutdown()
    print('shut down queue')
    for t in threads:
        t.join()

if __name__ == "__main__":
    main(sys.argv[1:])
