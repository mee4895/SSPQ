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

queue = asyncio.Queue()


async def user_handler(reader, writer):
    user_address = writer.get_extra_info('peername')
    if LOG_LEVEL >= LogLevel.INFO:
        print('User{} connected'.format(str(user_address)))

    while True:
        try:
            msg = await read_message(reader)
        except MessageException as e:
            if LOG_LEVEL >= LogLevel.WARN:
                print('User{} disconnected because: {}'.format(str(user_address), str(e)))
            writer.close()
            return
        except EOFError:
            if LOG_LEVEL >= LogLevel.INFO:
                print('User{} disconnected'.format(str(user_address)))
            writer.close()
            return

        if LOG_LEVEL >= LogLevel.DBUG:
            print('Recieved: ' + msg.payload.decode())


# Entry Point
if __name__ == "__main__":
    # Setup argparse
    parser = ArgumentParser(description='SSPQ - Super Simple Python Queue', add_help=True)
    parser.add_argument('--host', action='store', default='127.0.0.1', required=False, help='Set the host address. Juse 0.0.0.0 to make the server public', dest='host', metavar='<host>')
    parser.add_argument('-p', '--port', action='store', default='8888', type=int, required=False, help='Set the port the server listens to', dest='port', metavar='<port>')
    parser.add_argument('-ll', '--loglevel', action='store', default='info', type=LogLevel.parse, choices=[
        LogLevel.FAIL,
        LogLevel.WARN,
        LogLevel.INFO,
        LogLevel.DBUG
    ], required=False, help='Set the appropriate log level for the output on stdout. Possible values are: [ fail | warn | info | dbug ]', dest='log_level', metavar='<log-level>')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s v.0.0.0')
    args = parser.parse_args()

    # Use all the arguments
    LOG_LEVEL = args.log_level
    HOST = args.host
    PORT = args.port

    # Setup asyncio
    loop = asyncio.get_event_loop()
    coro = asyncio.start_server(user_handler, HOST, PORT, loop=loop)
    server = loop.run_until_complete(coro)

    # Serve requests until Ctrl+C is pressed
    print('Serving on {}'.format(server.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    # Close the server
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()
