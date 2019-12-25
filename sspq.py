"""
This is all the basic library code used to setup a client for a sspq message
queue connection. The code here is all asyncio based and can't really be run
without a propper event loop.
"""
import asyncio
from enum import Enum


__all__ = [
    'Client',
    'ClientStateException',
    'MAGIC_VALUE',
    'MessageType',
    'MessageException',
    'Message',
    'read_message',
    'ServerStateException',
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



#
# --- Exceptions ---
#
class MessageException(Exception):
    """
    This is raised if a message is not propperly detected.
    """
    def __init__(self, message):
        super().__init__(message)


class ServerStateException(Exception):
    """
    This is raised if the server blocks the client or sends unsupported messages.
    """
    def __init__(self, msg: str):
        super().__init__(msg)


class ClientStateException(Exception):
    """
    This is raised if the client is in a incorrect state for the requested
    operation.
    """
    def __init__(self, msg: str):
        super().__init__(msg)



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


class Client():
    """
    This class is used to comunicate with the server.
    """
    def __init__(self):
        self.connected = False
        self.receiving = False

    async def connect(self, host: str='127.0.0.1', port: int=SSPQ_PORT, loop=None) -> None:
        """
        This function connects the client to the server specified in the params
        """
        if self.connected:
            raise ClientStateException('Already connected!')

        self.reader, self.writer = await asyncio.open_connection(host=host, port=port, loop=loop)
        self.connected = True

    async def send(self, message: bytes, retrys: int=3) -> None:
        """
        This function is used to send data packages to the queue. It can be used
        in any connected state of the client.
        """
        if not self.connected:
            raise ClientStateException('Need to connect first!')

        msg = Message(MessageType.SEND, retrys, len(message), message)
        await msg.send(self.writer)

    async def receive(self, dead: bool=False) -> bytes:
        """
        This function is used to get a package from the queue. It is blocking
        until the data is received.
        """
        if not self.connected:
            raise ClientStateException('Need to connect first!')
        if self.receiving:
            raise ClientStateException('Can\'t receive a new package while still working on an old one.')

        # tell the server the client is ready to receive
        msg = Message(MessageType.RECEIVE if not dead else MessageType.DEAD_RECEIVE)
        await msg.send(self.writer)
        self.receiving = True

        # receive and process the message
        msg = await read_message(self.reader)
        if msg.type == MessageType.SEND:
            return msg.payload
        elif msg.type == MessageType.NO_RECEIVE:
            if dead:
                raise ServerStateException('Server has no dead letter queue')
            else:
                raise ServerStateException('Server blocks client from receiving')
        else:
            raise ServerStateException('Server answerd with an unknown package')

    async def confirm(self) -> None:
        """
        This function confirms the finished processing of the message and finally
        removes it from the queue server.
        """
        if not self.connected:
            raise ClientStateException('Need to connect first!')
        if not self.receiving:
            raise ClientStateException('No package to confirm')

        # confirm the last package to the server
        msg = Message(MessageType.CONFIRM)
        await msg.send(self.writer)
        self.receiving = False

    async def disconnect(self) -> None:
        """
        This function disconnects the client from the server.
        """
        if not self.connected:
            raise ClientStateException('Need to connect first!')

        await self.writer.drain()
        self.writer.close()
        await self.writer.wait_closed()
        self.connected = False



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
