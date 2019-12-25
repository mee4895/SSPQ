import asyncio
from sspq import *
from argparse import ArgumentParser



async def _receive_msg(host: str='127.0.0.1', port: int=SSPQ_PORT, nac: bool=False, dead: bool=False, loop=None) -> None:
    """
    This should only be used by the cli as a helper function to receive messages.
    """
    client = Client()
    await client.connect(host=host, port=port, loop=loop)
    if client.connected:
        print(f'Connected to {(host, port)}')

    while True:
        msg = await client.receive(dead=dead)
        print('Message:')
        print(msg.decode())
        if not nac:
            await client.confirm()
            print('(Auto-confirmed message)')
        if msg.decode() == 'kill':
            break
    await client.disconnect()



# Entry Point for the cli
if __name__ == "__main__":
    # Setup argparse
    parser = ArgumentParser(description='SSPQ Blackhole Client - Super Simple Python Queue Client', add_help=True)
    parser.add_argument('-R', '-dr', '--dead-receive', action='store_true', default=False, required=False, help='Flag if you want to receive data from the dead letter queue', dest='dead')
    parser.add_argument('-a', '--address', action='store', default='127.0.0.1', required=False, help='Set the server address to connect to.', dest='host', metavar='<address>')
    parser.add_argument('-p', '--port', action='store', default=SSPQ_PORT, type=int, required=False, help='Set the port the server listens to', dest='port', metavar='<port>')
    parser.add_argument('-nac', '--no-auto-confirm', action='store_true', default=False, required=False, help='Disable auto confirm. WARNING this automatically requeues the message since the conection is terminated after the command finishes', dest='nac')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s v1.0.0')
    args = parser.parse_args()

    # setup asyncio
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(_receive_msg(loop=loop, **args.__dict__))
    except KeyboardInterrupt:
        pass
    loop.close()
