from serial import Serial
import struct
from message import Message
from readerWriter import ReaderWriter
from messageQueue import MessageQueue

class SerialReaderWriter(ReaderWriter): 

    class ShutdownException(Exception):
        pass

    def __init__(self, port : str, baud : int, timeout : float, messageQueue : MessageQueue) -> None:
        self.ser : Serial = Serial(port=port, baudrate=baud, timeout=timeout)
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        self.messageQueue = messageQueue

    def readBytes(self, num_bytes : int):
        read_bytes = b''
        while self.messageQueue.isRunning() and len(read_bytes) < num_bytes:
            read_bytes += self.ser.read(num_bytes - len(read_bytes))

        if not self.messageQueue.isRunning():
            raise SerialReaderWriter.ShutdownException("Message Queue stopped running")

        return read_bytes

    def writeMessage(self, message : Message):
        self.ser.write(message.get_as_bytes())
        

##### READ FROM THE SERIAL PORT for incoming messages
    def readMessage(self) -> Message:
        potentialMessage = Message(new=False)

        try:
            data = self.readBytes(MAX_MESSAGE_SIZE)
        except TimeoutError:
            return None
        except SerialReaderWriter.ShutdownException as s:
            return None
        potentialMessage.set_msg_id(struct.unpack(">H", data[:2])[0])
        potentialMessage.set_purpose(struct.unpack(">B", data[2])[0])
        potentialMessage.number = struct.unpack(">B", data[3])[0]
        potentialMessage.set_size(struct.unpack(">L", data[4:8])[0])

        if potentialMessage.size_of_payload > MAX_MESSAGE_SIZE:
            print(f"--Error: buffer? ID: {potentialMessage.msg_id}, purpose: {potentialMessage.purpose}, num: {potentialMessage.number}, len_payload: {potentialMessage.size_of_payload}")
            
        potentialMessage.set_payload(data[8:8+potentialMessage.size_of_payload])

        checksum = data[-1]
        same_checksums, calculated_checksum = Message.test_checksum(bytestring=potentialMessage.get_as_bytes()[:-1], checksum=checksum)

        if not same_checksums:    
            print(f"--Error: checksum. Received checksum: {checksum} | calculated checksum: {calculated_checksum}. {potentialMessage}")
            return None

        return potentialMessage
