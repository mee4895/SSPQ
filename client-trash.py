import asyncio
from sspq import *



async def _send_msg(loop=None):
    """
    This should only be used by the cli as a helper function to send messages.
    """
    client = Client()
    await client.connect(host='127.0.0.1', port=8888, loop=loop)

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
    loop.run_until_complete(_send_msg(loop=loop))
    loop.close()
