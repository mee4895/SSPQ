import asyncio
from sspq import Message, MessageType, read_message, SSPQ_PORT
from argparse import ArgumentParser


__all__ = [
    'ServerStateException',
    'ClientStateException',
    'Client'
]


class ServerStateException(Exception):
    def __init__(self, msg: str):
        super(msg)


class ClientStateException(Exception):
    def __init__(self, msg: str):
        super(msg)


class Client():
    def __init__(self):
        self.connected = False
        self.receiving = False

    async def connect(self, host: str='127.0.0.1', port: int=SSPQ_PORT, loop=None):
        if self.connected:
            raise ClientStateException('Already connected!')

        self.reader, self.writer = await asyncio.open_connection(host=host, port=port, loop=loop)
        self.connected = True

    async def send(self, message: bytes, retrys: int=3) -> None:
        if not self.connected:
            raise ClientStateException('Need to connect first!')

        msg = Message(MessageType.SEND, retrys, len(message), message)
        await msg.send(self.writer)

    async def receive(self, dead: bool=False) -> bytes:
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
        if not self.connected:
            raise ClientStateException('Need to connect first!')
        if not self.receiving:
            raise ClientStateException('No package to confirm')

        # confirm the last package to the server
        msg = Message(MessageType.CONFIRM)
        await msg.send(self.writer)
        self.receiving = False

    def disconnect(self) -> None:
        if not self.connected:
            raise ClientStateException('Need to connect first!')

        self.writer.close()
        # Only available in python 3.7 add this later
        #await self.writer.wait_closed()
        self.connected = False


async def _send_msg(message: str, host: str, port: int, retrys: int, loop):
    client = Client()
    await client.connect(host=host, port=port, loop=loop)
    await client.send(message.encode(), retrys=retrys)
    client.disconnect()


async def _receive_msg(host: str, port: int, nac: bool, dead: bool, loop):
    client = Client()
    await client.connect(host=host, port=port, loop=loop)
    msg = await client.receive(dead=dead)
    print('Message:')
    print(msg.decode())
    if not nac:
        await client.confirm()
        print('(Auto-confirmed message)')
    client.disconnect()


# Entry Point
if __name__ == "__main__":
    # Setup argparse
    parser = ArgumentParser(description='SSPQ Client - Super Simple Python Queue Client', add_help=True)
    parser.add_argument('-s', '--send', action='store_true', required=False, help='Flag if you want to send data to the queue', dest='send')
    parser.add_argument('-r', '--receive', action='store_true', required=False, help='Flag if you want to receive data from the queue', dest='receive')
    parser.add_argument('-R', '-dr', '--dead-receive', action='store_true', required=False, help='Flag if you want to receive data from the dead letter queue', dest='dead_receive')
    parser.add_argument('-a', '--address', action='store', default='127.0.0.1', required=False, help='Set the server address to connect to.', dest='host', metavar='<address>')
    parser.add_argument('-p', '--port', action='store', default=SSPQ_PORT, type=int, required=False, help='Set the port the server listens to', dest='port', metavar='<port>')
    parser.add_argument('-m', '--message', action='store', default='', required=False, help='Set the message to send', dest='message', metavar='<message>')
    parser.add_argument('--retrys', action='store', default='3', type=int, choices=range(0,256), required=False, help='Set the amount of retrys for failed messages. A value of 255 is used to indicate infinite retrys.', dest='retrys', metavar='[0-255]')
    parser.add_argument('-nac', '--no-auto-confirm', action='store_true', required=False, help='Disable auto confirm. WARNING this automatically requeues the message since the conection is terminated after the command finishes', dest='nac')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s v0.3.0')
    args = parser.parse_args()

    # check args
    if args.send and args.message == '':
        parser.error('The usage of empty messages is discuraged. Please add a message!')

    # setup asyncio
    loop = asyncio.get_event_loop()
    if args.send:
        loop.run_until_complete(_send_msg(args.message, host=args.host, port=args.port, retrys=args.retrys, loop=loop))
    if args.receive:
        loop.run_until_complete(_receive_msg(host=args.host, port=args.port, nac=args.nac, dead=False, loop=loop))
    if args.dead_receive:
        loop.run_until_complete(_receive_msg(host=args.host, port=args.port, nac=args.nac, dead=True, loop=loop))
    loop.close()
