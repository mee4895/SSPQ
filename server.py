import asyncio
from enum import Enum
from sspq import Message, MessageType, MessageException, read_message, SSPQ_PORT
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
        string = string.lower()
        if string == 'fail':
            return cls.FAIL
        if string == 'warn':
            return cls.WARN
        if string == 'info':
            return cls.INFO
        if string == 'dbug':
            return cls.DBUG
        raise ArgumentTypeError(str + ' is NOT a valid loglevel')


async def user_handler(reader, writer):
    client_address = writer.get_extra_info('peername')
    if LOG_LEVEL >= LogLevel.INFO:
        print('User{} connected'.format(str(client_address)))

    client_data = {
        'writer': writer,
        'current_msg': None
    }

    while True:
        try:
            msg = await read_message(reader)
        except MessageException as e:
            if LOG_LEVEL >= LogLevel.WARN:
                print('User{} disconnected because: {}'.format(str(client_address), str(e)))
            writer.close()
            return
        except EOFError:
            if LOG_LEVEL >= LogLevel.INFO:
                print('User{} disconnected'.format(str(client_address)))
            writer.close()
            return

        if msg.type == MessageType.SEND:
            if LOG_LEVEL >= LogLevel.DBUG:
                print('Recieved: ' + msg.payload.decode())
            await message_queue.put(msg)
        elif msg.type == MessageType.RECEIVE:
            if client_data['current_msg'] is not None:
                if LOG_LEVEL >= LogLevel.WARN:
                    print('Receive Message is going to be droped because client need to confirm his message.')
                    continue
            if LOG_LEVEL >= LogLevel.DBUG:
                print('User{} wants to receive'.format(str(client_address)))
            await client_queue.put(client_data)
        elif msg.type == MessageType.CONFIRM:
            if client_data['current_msg'] is None:
                if LOG_LEVEL >= LogLevel.WARN:
                    print('Confirm Message is going to be droped because client has no message to confirm.')
                    continue
            if LOG_LEVEL >= LogLevel.DBUG:
                print('User{} confirms message'.format(str(client_address)))
            client_data['current_msg'] = None
            await asyncio.sleep(0)
        else:
            if LOG_LEVEL >= LogLevel.WARN:
                print('Received unknown packet:\n' + msg.encode().decode())


async def queue_handler():
    while True:
        client = await client_queue.get()
        msg = await message_queue.get()
        client['current_msg'] = msg
        await msg.send(client['writer'])


# Entry Point
if __name__ == "__main__":
    # Setup argparse
    parser = ArgumentParser(description='SSPQ Server - Super Simple Python Queue Server', add_help=True)
    parser.add_argument('--host', action='store', default='127.0.0.1', required=False, help='Set the host address. Juse 0.0.0.0 to make the server public', dest='host', metavar='<host>')
    parser.add_argument('-p', '--port', action='store', default=SSPQ_PORT, type=int, required=False, help='Set the port the server listens to', dest='port', metavar='<port>')
    parser.add_argument('-ll', '--loglevel', action='store', default='info', type=LogLevel.parse, choices=[
        LogLevel.FAIL,
        LogLevel.WARN,
        LogLevel.INFO,
        LogLevel.DBUG
    ], required=False, help='Set the appropriate log level for the output on stdout. Possible values are: [ fail | warn | info | dbug ]', dest='log_level', metavar='<log-level>')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s v.0.1.0')
    args = parser.parse_args()

    # Use all the arguments
    LOG_LEVEL = args.log_level
    HOST = args.host
    PORT = args.port

    # Setup asyncio & queues
    loop = asyncio.get_event_loop()
    message_queue = asyncio.Queue(loop=loop)
    client_queue = asyncio.Queue(loop=loop)
    coro = asyncio.start_server(user_handler, HOST, PORT, loop=loop)
    server = loop.run_until_complete(coro)
    queue_worker = asyncio.ensure_future(queue_handler(), loop=loop)

    # Serve requests until Ctrl+C is pressed
    print('Serving on {}'.format(server.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    # Close the server
    server.close()
    queue_worker.cancel()
    loop.run_until_complete(server.wait_closed())
    loop.close()
