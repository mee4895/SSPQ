import asyncio
from enum import Enum
from sspq import *


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

LOG_LEVEL = LogLevel.DBUG

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


def main():
    # Setup asyncio
    loop = asyncio.get_event_loop()
    coro = asyncio.start_server(user_handler, '127.0.0.1', 8888, loop=loop)
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

# Enty Hook
if __name__ == "__main__":
    main()
