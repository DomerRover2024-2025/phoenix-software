import struct
import socket

from message import Message, MAX_MESSAGE_SIZE
from readerWriter import ReaderWriter
from messageQueue import MessageQueue

class SocketReaderWriter(ReaderWriter):
    
    def __init__(self, host, port, messageQueue : MessageQueue, rover : bool):
        self.messageQueue = messageQueue
        self.communicator = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.communicator.settimeout(1.0)
        self.target_addr = (host, port)

        if rover:
            self.communicator.bind((host, port))

    def writeMessage(self, message : Message):
        self.communicator.sendto(message.get_as_bytes(), self.target_addr)

    def readBytes(self, num_bytes : int):
        data, self.target_addr = self.communicator.recvfrom(MAX_MESSAGE_SIZE)
        return data

    def readMessage(self) -> Message:
        potentialMessage = Message(new=False)

        try:
            data = self.readBytes(MAX_MESSAGE_SIZE)
        except TimeoutError:
            return None

        potentialMessage.set_msg_id(struct.unpack(">H", data[:2])[0])
        potentialMessage.set_purpose(struct.unpack(">B", data[2:3])[0])
        potentialMessage.number = struct.unpack(">B", data[3:4])[0]
        potentialMessage.set_size(struct.unpack(">L", data[4:8])[0])

        if potentialMessage.size_of_payload > MAX_MESSAGE_SIZE:
            print(f"--Error: buffer? ID: {potentialMessage.msg_id}, purpose: {potentialMessage.purpose}, num: {potentialMessage.number}, len_payload: {potentialMessage.size_of_payload}")

        potentialMessage.set_payload(data[8:8+potentialMessage.size_of_payload])

        checksum = data[-1]
        same_checksums, calculated_checksum = Message.test_checksum(bytestring=potentialMessage.get_as_bytes()[:-1], checksum=checksum.to_bytes(1))

        if not same_checksums:    
            print(f"--Error: checksum. Received checksum: {checksum} | calculated checksum: {calculated_checksum}. {potentialMessage}")
            return None

        return potentialMessage
