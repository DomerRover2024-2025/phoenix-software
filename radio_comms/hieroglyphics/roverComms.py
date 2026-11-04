# This is the server side of a client-server model.
# This will be receiving requests from the base station.

###################
##### IMPORTS #####
###################

from serial import Serial
import cv2
import os
import struct
import argparse
import numpy as np
import threading
import time
import sys

from message import Message
from scheduler import Scheduler
from messageQueue import MessageQueue
from roverMessageProcessor import RoverMessageProcessor
from socketReaderWriter import SocketReaderWriter
from serialReaderWriter import SerialReaderWriter
from readerWriter import ReaderWriter
from concurrentSet import ConcurrentSet

def main(args):
    if len(args) > 0:
        port = args[0]
    else:
        port = '/dev/ttyUSB0'

    if len(args) > 1:
        host = args[1]
    else:
        host = 'localhost'
    baud = 57600
    timeout = 0.1

    # respective 'int' identifiers for each topic
    topics = {
        'status': 3,
        'vid_feed': 10,
        'position': 1,
        'hdp': 1,
        'ldp': 1,
        'file': 1
    }

    messageQueue : MessageQueue = MessageQueue()
    # readerWriter : ReaderWriter = SerialReaderWriter(port, baud, timeout, messageQueue)
    readerWriter : ReaderWriter = SocketReaderWriter(host, 9998, messageQueue, rover=True)
    scheduler = Scheduler(readerWriter=readerWriter, topics=topics)

    scheduler_thread = threading.Thread(target=scheduler.sendMessages, args=(messageQueue,))
    process_messages_thread = threading.Thread(target=process_messages, args=(messageQueue, scheduler))
    threads = [scheduler_thread, process_messages_thread]
    # future_video = executor.submit(capture_video)

    for t in threads:
        t.start()

    print('entering read loop')

    received_info_from_gnss_eh = False
    
    try:
        while True:
            message = readerWriter.readMessage()
            if message:
                messageQueue.append(message)
                print(f'message added to queue of purpose {message.purpose.name}')

    except KeyboardInterrupt:
        pass
    # except Exception as e:
    #     print('rover reading: ', e)
        
    messageQueue.shutdown()
    for t in threads:
        t.join()

# capture_video_eh = False

def process_messages(messageQueue : MessageQueue, scheduler : Scheduler) -> None:
    print('thread activated :)')

    # rclpy.init(args=None)
    # #create node
    # talkerNode = TalkerNode()

    # TODO: TODO TODO FIX THIS when connected to the jetson
    #arduino = serial.Serial('/dev/ttyACM0')

    MSG_LOG = 'messages_rover.log'
    open(MSG_LOG, 'w').close()

    VID_WIDTH = 200
    CAM_PATHS = [
        '/dev/v4l/by-id/usb-046d_081b_32750F50-video-index0',
        '/dev/v4l/by-id/usb-Technologies__Inc._ZED_2i_OV0001-video-index0'
    ]

    # TODO: Change these lines out when trying to write to the motors.
    # arduinoPath = '/dev/ttyACMO'
    arduinoPath = None

    messageProcessor = RoverMessageProcessor(MSG_LOG, scheduler, arduinoPath)

    # we are guaranteed only a certain number of outgoing messages.
    alreadyProcessedMessages = ConcurrentSet()
    oldSetOfProcessedMessages = ConcurrentSet()

    while messageQueue.isRunning():

        currentMessage = messageQueue.pop()

        if currentMessage is None:
            continue

        Message.log_message(currentMessage, MSG_LOG)

        if currentMessage.purpose == Message.Purpose.ACK:
            messageProcessor.handleAcknowledgment(currentMessage)
            continue

        acknowledgment = messageProcessor.generateAcknowledgment(currentMessage) 
        scheduler.addMessage(acknowledgment, 'acknowledgment')

        if currentMessage.msg_id in alreadyProcessedMessages or currentMessage.msg_id in oldSetOfProcessedMessages:
            continue

        alreadyProcessedMessages.add(currentMessage.msg_id)

        if len(alreadyProcessedMessages) >= Scheduler.BUFFER_BOUND:
            oldSetOfProcessedMessages = alreadyProcessedMessages
            alreadyProcessedMessages = ConcurrentSet()

        if currentMessage.purpose == Message.Purpose.ERROR:
            messageProcessor.handleDebugMessage(currentMessage)

        elif currentMessage.purpose == Message.Purpose.MOVEMENT:
            messageProcessor.handleDrivingMessage(currentMessage)

        elif currentMessage.purpose == Message.Purpose.VIDEO:
            messageProcessor.handleVideoToggleMessage(currentMessage) 

        elif currentMessage.purpose == Message.Purpose.HIGH_DEFINITION_PHOTO: 
            messageProcessor.handleHighDefPhotoRequestMessage(currentMessage)

        elif currentMessage.purpose == Message.Purpose.LOW_DEFINITION_PHOTO:
            messageProcessor.handleLowDefPhotoRequestMessage(currentMessage)

        elif currentMessage.purpose == Message.Purpose.FILE_CONTENTS:
            messageProcessor.handleFileContentsRequestMessage(currentMessage)

        else:
            print('--Error: message matched no known purposes.')
        # except Exception as e:
        #    print('--error(process messages): ', e)
        messageProcessor.imageCapturer.stopTakingVideo()

# import rclpy
# from rclpy.node import Node
# from std_msgs.msg import String
# #be able to write to the arduino serial port
# #create an instance of the serial, open up a serial.write, and then write whatever the message being published is
# class TalkerNode(Node):
#     def __init__(self):
#         super().__init__('talker_node')
#         # TODO change the topic here from 'motor_state'
#         self.publisher_ = self.create_publisher(String, 'motor_state', 10)
#         timer_period = 0.1
#         #self.timer = self.create_timer(timer_period, self.timer_callback)
#         self.count = 0
#         self.serialPort = serial.Serial('/dev/ttyACM0')
#     def listener_callback(self, msg):
#         #msg = String()
#         #msg.data = f'Hello everyone {self.count}'
#         # self.publisher_.publish(msg.data)
#         self.count += 1
#         self.get_logger().info(f'Recieving {msg.data}')
#         # self.write(msg.data)
#      #def write(x):
#         self.serialPort.write(msg.data.encode())

if __name__ == '__main__':
    main(sys.argv[1:])
