import asyncio
from sspq import Message, MessageType


async def tcp_echo_client(message, loop):
    reader, writer = await asyncio.open_connection('127.0.0.1', 8888,
                                                   loop=loop)

    print('Send: %r' % message)
    msg = Message(MessageType.SEND, 1, 300, len(message), message.encode())
    await msg.send(writer)
    await msg.send(writer)

    #data = await reader.read(100)
    #print('Received: %r' % data.decode())

    print('Close the socket')
    writer.close()


message = 'Hello World!'
loop = asyncio.get_event_loop()
loop.run_until_complete(tcp_echo_client(message, loop))
loop.close()
