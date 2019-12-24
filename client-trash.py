import asyncio
from sspq import Message, MessageType, read_message, SSPQ_PORT
from argparse import ArgumentParser


__all__ = [
    'ServerStateException',
    'ClientStateException',
    'Client'
]


class ServerStateException(Exception):
    """
    Exception to indicate a error on the server side.
    """
    def __init__(self, msg: str):
        super().__init__(msg)


class ClientStateException(Exception):
    """
    Exception to indicate a error in the state of the client. Mostly this is
    used if messages are not correctly confirmed.
    """
    def __init__(self, msg: str):
        super().__init__(msg)


class Client():
    """
    This class is used to comunicate with the server.
    """
    def __init__(self):
        self.connected = False
        self.receiving = False

    async def connect(self, host: str='127.0.0.1', port: int=SSPQ_PORT, loop=None):
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

    async def confirm(self):
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


async def _send_msg():
    """
    This should only be used by the cli as a helper function to send messages.
    """
    client = Client()
    await client.connect(host='127.0.0.1', port=8888)

    for i in range(1, 100):
        #with open('testdata/10K.base64', 'rb') as file:
        #    await client.send(file.read() + bytes(i), retrys=3)
        await client.send(('Data: ' + str(i)).encode())
        print(i)
        #await asyncio.sleep(0.00001)
    await client.disconnect()

# Entry Point for the cli
if __name__ == "__main__":
    # setup asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_send_msg())
    loop.close()
