import asyncio
from sspq import *
from argparse import ArgumentParser



async def _send_msg(message: str, host: str, port: int, retrys: int):
    client = Client()
    await client.connect(host=host, port=port)
    await client.send(message.encode(), retrys=retrys)
    await client.disconnect()


async def _receive_msg(host: str, port: int, nac: bool, dead: bool):
    client = Client()
    await client.connect(host=host, port=port)
    msg = await client.receive(dead=dead)
    print('Message:')
    print(msg.decode())
    if not nac:
        await client.confirm()
        print('(Auto-confirmed message)')
    await client.disconnect()



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
    parser.add_argument('-v', '--version', action='version', version='%(prog)s v1.0.0')
    args = parser.parse_args()

    # check args
    if args.send and args.message == '':
        parser.error('The usage of empty messages is discuraged. Please add a message!')

    # setup asyncio
    loop = asyncio.get_event_loop()
    if args.send:
        loop.run_until_complete(_send_msg(args.message, host=args.host, port=args.port, retrys=args.retrys))
    if args.receive:
        loop.run_until_complete(_receive_msg(host=args.host, port=args.port, nac=args.nac, dead=False))
    if args.dead_receive:
        loop.run_until_complete(_receive_msg(host=args.host, port=args.port, nac=args.nac, dead=True))
    loop.close()
