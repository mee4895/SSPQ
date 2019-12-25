"""
This is all the basic library code used to setup a client for a sspq message
queue connection. The code here is all asyncio based and can't really be run
without a propper event loop.
"""
import asyncio
from enum import Enum


__all__ = [
    'LogLevel',
    'MAGIC_VALUE',
    'MessageType',
    'MessageException',
    'Message',
    'read_message',
    'SSPQ_PORT'
]



#
# --- Constants ---
#
MAGIC_VALUE = b'\x55\x99'
SSPQ_PORT = 8888



#
# --- Enum Definitions ---
#
class OrderedEnum(Enum):
    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.value >= other.value
        return NotImplemented
    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.value > other.value
        return NotImplemented
    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.value <= other.value
        return NotImplemented
    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented


class MessageType(Enum):
    SEND = b'\x5e'
    RECEIVE = b'\xec'
    CONFIRM = b'\xc0'
    DEAD_RECEIVE = b'\xde'
    NO_RECEIVE = b'\x0e'

    OTHER = b'\xff'

    @classmethod
    def get(cls, value: bytes) -> super:
        try:
            return cls(value)
        except ValueError:
            return cls.OTHER


class LogLevel(OrderedEnum):
    FAIL = '1'
    WARN = '2'
    INFO = '3'
    DBUG = '4'

    @classmethod
    def parse(cls, string: str) -> super:
        _string = string.lower()
        if _string == 'fail':
            return cls.FAIL
        if _string == 'warn':
            return cls.WARN
        if _string == 'info':
            return cls.INFO
        if _string == 'dbug':
            return cls.DBUG
        raise ArgumentTypeError(string + ' is NOT a valid loglevel')



#
# --- Exceptions ---
#
class MessageException(Exception):
    """
    This is raised if a message is not propperly detected.
    """
    def __init__(self, message):
        super().__init__(message)



#
# --- Classes ---
#
class Message():
    """
    This is a message which is sent via a sspq server.
    """
    def __init__(self, type: MessageType, retries: int = 0, payload_size: int = 0, payload: bytes = b''):
        self.type = type
        self.retries = retries
        self.payload_size = payload_size
        self.payload = payload

    def encode(self) -> bytes:
        """
        This encodes the message as a bytes object to be sent over the network
        or write to disk.
        """
        return MAGIC_VALUE + \
            self.type.value + \
            self.retries.to_bytes(1, 'big', signed=False) + \
            self.payload_size.to_bytes(4, 'big', signed=False) + \
            self.payload

    async def send(self, writer: asyncio.StreamWriter) -> None:
        """
        This sends the message via the given asyncio StreamWriter.
        """
        writer.write(self.encode())
        await writer.drain()


class Server_Client():
    """
    This represents a client connected to a server.
    """
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, loop):
        self.reader = reader
        self.writer = writer
        self.address = writer.get_extra_info('peername')
        self.message = None
        self.disconnected = False
        self.message_event = asyncio.Event(loop=loop)



#
# --- Functions ---
#
async def read_message(reader: asyncio.StreamReader) -> Message:
    """
    This function reads exacly one message from the asyncio.StreamReader and
    returns it as a Message. A MessageException is raised when the magic value
    check fails.
    """
    mv = await reader.read(n=2)
    if mv != MAGIC_VALUE:
        if mv == b'':
            raise EOFError()
        else:
            raise MessageException('Magic value check failed')

    _type = await reader.read(n=1)
    type = MessageType.get(_type)
    _retries = await reader.read(n=1)
    retries = int.from_bytes(_retries, byteorder='big', signed=False)
    _payload_size = await reader.read(n=4)
    payload_size = int.from_bytes(_payload_size, byteorder='big', signed=False)
    payload = await reader.read(n=payload_size)

    return Message(type=type, retries=retries, payload_size=payload_size, payload=payload)
