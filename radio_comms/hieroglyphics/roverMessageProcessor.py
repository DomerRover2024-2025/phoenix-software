from serial import Serial
import struct

from imageCapturer import ImageCapturer
from scheduler import Scheduler
from message import Message
from messageProcessor import MessageProcessor

class RoverMessageProcessor:

    VIDEO_WIDTH=200 

    def __init__(self, log : str, scheduler : Scheduler, arduinoPath='/dev/ttyACM0', cameraPaths=0):
        self.messageProcessor = MessageProcessor(log, scheduler)
        if arduinoPath:
            self.arduino = Serial(arduinoPath)
        else:
            self.arduino = None
        self.imageCapturer = ImageCapturer(cameraPaths)

    def generateAcknowledgment(self, message : Message) -> Message:
        return self.messageProcessor.generateAcknowledgment(message)

    def handleAcknowledgment(self, message : Message):
        self.messageProcessor.handleAcknowledgment(message)

    def handleDebugMessage(self, message : Message):
        self.messageProcessor.handleDebugMessage(message)

    def handleDrivingMessage(self, message : Message):
        payload = message.get_payload()
        lspeed = struct.unpack('>h', payload[0:2])[0]
        rspeed = struct.unpack('>h', payload[2:4])[0]
        '''
        speed_scalar = struct.unpack('>f', payload[4:8])[0]
        cam_left = struct.unpack('>B', payload[8:9])[0]
        cam_right = struct.unpack('>B', payload[9:10])[0]
        button_x = struct.unpack('>B', payload[10:11])[0]
        button_y = struct.unpack('>B', payload[11:12])[0]
        '''

        floatString = f'{lspeed} {rspeed}'
        print(floatString, 'speeds')
        if self.arduino:
            self.arduino.write(floatString.encode())

    # TODO: This currently just sends a single frame.
    # This ought to query the true camera, and have it continue to send photos back here.
    # This may require harder integration...
    def handleVideoToggleMessage(self, message : Message):
        cameraNumber = struct.unpack('>b', message.get_payload())[0] 
        if cameraNumber == -1:
            self.imageCapturer.stopTakingVideo()

        self.imageCapturer.startTakingVideo()
        self.changeCamera(cameraNumber)

    def handleHighDefPhotoRequestMessage(self, message : Message):
        length, buffer = self.imageCapturer.captureImage(90)
        print('Image captured')
        if buffer is None:
            print('error no image could be grabbed')
            errorString = 'Error: could not capture a high definition photo.'
            self.messageProcessor.addListOfMessages(Message(purpose=Message.Purpose.ERROR, payload=error_str.encode()), 'status')

        print('splitting messages')
        msgs = Message.message_split(big_payload=buffer.tobytes(), purpose_for_all=Message.Purpose.HIGH_DEFINITION_PHOTO)
        print('messages split')
        self.messageProcessor.addListOfMessages(msgs, 'hdp')
        print('Message added of length ', len(buffer.tobytes()))

    def handleLowDefPhotoRequestMessage(self, message : Message):
        print('getting an ldp photo')
        _, buffer = self.imageCapturer.captureImage(90, self.VIDEO_WIDTH)
        if buffer is None:
            error_str = 'Error: could not capture hdp.'
            print(error_str)
            self.messageProcessor.addMessage(Message(purpose=Message.Purpose.ERROR, payload=error_str.encode()), 'status')
            return

        msgs = Message.message_split(big_payload=buffer.tobytes(), purpose_for_all=Message.Purpose.LOW_DEFINITION_PHOTO)
        self.messageProcessor.addListOfMessages(msgs, 'ldp')
        print('Message added of length ', len(buffer.tobytes()))

    def handleFileContentsRequestMessage(self, message : Message):
        path = message.get_payload().decode()
        if not os.path.exists(path):
            error_str = f'--Error: filepath {path} does not exist.'
            print(error_str)
            self.messageProcessor.addMessage(Message(purpose=Message.Purpose.ERROR, payload=error_str.encode()), 'status')
            return

        with open(path, 'rb') as f:
            contents = f.read()

        msg_title = Message(new=True, purpose=Message.Purpose.FILE_CONTENTS, number=1, payload=os.path.basename(path).encode())
        self.messageProcessor.addMessage(msg_title, 'file')
        self.messageProcessor.addListOfMessages(Message.message_split(purpose_for_all=Message.Purpose.FILE_CONTENTS, big_payload=contents, index_offset=1), 'file')

    def capture_video(self):
        while self.imageCapturer.isTakingVideo():
            self.imageCapturer.captureImage(30, ImageCapturer.VIDEO_WIDTH)

        self.messageProcessor.addListOfMessages(Message.message_split(big_payload=frame.tobytes(), purpose_for_all=Message.Purpose.VIDEO), 'vid_feed')

