import asyncio
from enum import Enum
from sspq import *
from argparse import ArgumentParser, ArgumentTypeError



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


class Server_Client():
    """
    This represents a client connected to a server.
    """
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.reader = reader
        self.writer = writer
        self.address = writer.get_extra_info('peername')
        self.message = None
        self.disconnected = False
        self.message_event = asyncio.Event()



def get_user_handler(retry_override: int=None):
    async def user_handler(reader, writer):
        client = Server_Client(reader=reader, writer=writer)
        if LOG_LEVEL >= LogLevel.INFO:
            print(f'User {client.address} connected')

        while True:
            try:
                msg = await read_message(client.reader)
            except MessageException as e:
                if LOG_LEVEL >= LogLevel.WARN:
                    print(f'User {client.address} disconnected because: {e}')
                client.disconnected = True
                client.message_event.set()
                client.writer.close()
                return
            except EOFError:
                if LOG_LEVEL >= LogLevel.INFO:
                    print(f'User {client.address} disconnected')
                client.disconnected = True
                client.message_event.set()
                client.writer.close()
                return

            if msg.type == MessageType.SEND:
                if LOG_LEVEL >= LogLevel.DBUG:
                    print('Recieved: ' + msg.payload.decode())
                if retry_override is not None:
                    msg.retries = retry_override
                await message_queue.put(msg)
            elif msg.type == MessageType.RECEIVE:
                if client.message is not None:
                    if LOG_LEVEL >= LogLevel.WARN:
                        print('Receive Message is going to be dropped because client need to confirm his message.')
                    continue
                if LOG_LEVEL >= LogLevel.DBUG:
                    print('User{} wants to receive'.format(str(client.address)))
                client.message_event.clear()
                await client_queue.put(client)
            elif msg.type == MessageType.CONFIRM:
                if client.message is None:
                    if LOG_LEVEL >= LogLevel.WARN:
                        print('Confirm Message is going to be dropped because client has no message to confirm.')
                    continue
                if LOG_LEVEL >= LogLevel.DBUG:
                    print('User{} confirms message'.format(str(client.address)))
                client.message = None
                client.message_event.set()
                await asyncio.sleep(0)
            elif msg.type == MessageType.DEAD_RECEIVE:
                if client.message is not None:
                    if LOG_LEVEL >= LogLevel.WARN:
                        print('Dead-Receive Message is going to be dropped because client need to confirm his message.')
                    continue
                if LOG_LEVEL >= LogLevel.DBUG:
                    print('User{} wants to dead receive'.format(str(client.address)))
                client.message_event.clear()
                await dead_letter_client_queue.put(client)
            else:
                if LOG_LEVEL >= LogLevel.WARN:
                    print('Received unknown packet:\n' + msg.encode().decode())
                await asyncio.sleep(0)
    return user_handler


async def message_handler(message: Message, client: Server_Client):
    client.message = message
    await message.send(client.writer)
    await client.message_event.wait()
    if client.message is not None:
        if client.message.retries == 0:
            if not NDLQ:
                await dead_letter_queue.put(client.message)
        else:
            if client.message.retries != 255:
                client.message.retries -= 1
            await message_queue.put(client.message)


async def queue_handler(loop):
    while True:
        msg = await message_queue.get()
        client = await client_queue.get()
        while client.disconnected:
            client = await client_queue.get()
        asyncio.ensure_future(message_handler(msg, client), loop=loop)


async def dead_letter_handler(message: Message, client: Server_Client):
    client.message = message
    await message.send(client.writer)
    await client.message_event.wait()
    if client.message is not None:
        await dead_letter_queue.put(message)


async def dead_letter_queue_handler(loop, active: bool=True):
    while True:
        if active:
            msg = await dead_letter_queue.get()
            client = await dead_letter_client_queue.get()
            while client.disconnected:
                client = await dead_letter_client_queue.get()
            asyncio.ensure_future(dead_letter_handler(msg, client), loop=loop)
        else:
            client = await dead_letter_client_queue.get()
            await Message(type=MessageType.NO_RECEIVE).send(client.writer)



# Entry Point
if __name__ == "__main__":
    # Setup argparse
    parser = ArgumentParser(description='SSPQ Server - Super Simple Python Queue Server', add_help=True)
    parser.add_argument('--host', action='store', default='127.0.0.1', required=False, help='Set the host address. Use 0.0.0.0 to make the server public', dest='host', metavar='<address>')
    parser.add_argument('-p', '--port', action='store', default=SSPQ_PORT, type=int, required=False, help='Set the port the server listens to', dest='port', metavar='<port>')
    parser.add_argument('-ll', '--loglevel', action='store', default='info', type=LogLevel.parse, choices=[
        LogLevel.FAIL, LogLevel.WARN, LogLevel.INFO, LogLevel.DBUG
    ], required=False, help='Set the appropriate log level for the output on stdout. Possible values are: [ fail | warn | info | dbug ]', dest='log_level', metavar='<level>')
    parser.add_argument('-ndlq', '--no-dead-letter-queue', action='store_true', required=False, help='Flag to dissable the dead letter queueing, failed packages are then simply dropped after the retries run out.', dest='ndlq')
    parser.add_argument('-r', '--force-retries', action='store', type=int, choices=range(0, 256), required=False, help='This overrides the retry values of all incoming packets to the given value. Values between 0 and 254 are possible retry values if 255 is used all packages are infinitely retried.', dest='retry', metavar='[0-255]')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s v1.0.0')
    args = parser.parse_args()

    # set 'global' log level
    LOG_LEVEL = args.log_level
    NDLQ = args.ndlq

    # Setup asyncio & queues
    loop = asyncio.get_event_loop()
    message_queue = asyncio.Queue()
    client_queue = asyncio.Queue()
    dead_letter_queue = asyncio.Queue()
    dead_letter_client_queue = asyncio.Queue()
    coro = asyncio.start_server(get_user_handler(retry_override=args.retry), args.host, args.port, loop=loop)
    server = loop.run_until_complete(coro)
    queue_worker = asyncio.ensure_future(queue_handler(loop=loop), loop=loop)
    dead_letter_queue_worker = asyncio.ensure_future(dead_letter_queue_handler(loop=loop, active=(not args.ndlq)), loop=loop)

    # Serve requests until Ctrl+C is pressed
    print(f'Serving on {server.sockets[0].getsockname()}')
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    # Close the server
    server.close()
    queue_worker.cancel()
    dead_letter_queue_worker.cancel()
    loop.run_until_complete(server.wait_closed())
    loop.close()
