import asyncio
from enum import Enum


__all__ = [
    'MessageType',
    'MessageException',
    'Message',
    'read_message'
]

MAGIC_VALUE = b'\x55\x99'


class MessageType(Enum):
    SEND = b'\x5e'
    RECEIVE = b'\xec'
    CONFIRM = b'\xc0'

    PING = b'\x91'
    PONG = b'\x90'

    OTHER = b'\xff'

    @classmethod
    def get(cls, value: bytes) -> super:
        try:
            return cls(value)
        except ValueError:
            return cls.OTHER


class MessageException(Exception):
    def __init__(self, message):
        super().__init__(message)


class Message():
    def __init__(self, type: MessageType, retrys: int, timeout: int, payload_size: int, payload: bytes):
        self.type = type
        self.retrys = retrys
        self.timeout = timeout
        self.payload_size = payload_size
        self.payload = payload

    def encode(self) -> bytes:
        return MAGIC_VALUE + \
            self.type.value + \
            self.retrys.to_bytes(1, 'big', signed=False) + \
            self.timeout.to_bytes(2, 'big', signed=False) + \
            self.payload_size.to_bytes(4, 'big', signed=False) + \
            self.payload

    async def send(self, writer: asyncio.StreamWriter) -> None:
        writer.write(self.encode())
        await writer.drain()


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

    b_type = await reader.read(n=1)
    type = MessageType.get(b_type)
    b_retrys = await reader.read(n=1)
    retrys = int.from_bytes(b_retrys, byteorder='big', signed=False)
    b_timeout = await reader.read(n=2)
    timeout = int.from_bytes(b_timeout, byteorder='big', signed=False)
    b_payload_size = await reader.read(n=4)
    payload_size = int.from_bytes(b_payload_size, byteorder='big', signed=False)
    payload = await reader.read(n=payload_size)

    return Message(type=type, retrys=retrys, timeout=timeout, payload_size=payload_size, payload=payload)
