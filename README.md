# SSPQ - The super simple python queue
> A quick messaging queue everywhere, there is python.


## Motivation:
The motivation for this project is to have a very simple light weight queue server which is easy to package with your application. This allows for quick and easy testing and development setups without the need for an installed full-blown messaging server.


## Prerequesits:
- python: >3.6 (should work with 3.5, but this is developed with and for 3.6)


## Usage:

### Server:
```
usage: server.py [-h] [--host <address>] [-p <port>] [-ll <level>] [-ndlq]
                 [-v]

SSPQ Server - Super Simple Python Queue Server

optional arguments:
  -h, --help            show this help message and exit
  --host <address>      Set the host address. Use 0.0.0.0 to make the server
                        public
  -p <port>, --port <port>
                        Set the port the server listens to
  -ll <level>, --loglevel <level>
                        Set the appropriate log level for the output on
                        stdout. Possible values are: [ fail | warn | info |
                        dbug ]
  -ndlq, --no-dead-letter-queue
                        Flag to dissable the dead letter queueing, failed
                        packages are then simply dropped after the retrys run
                        out.
  -v, --version         show program's version number and exit
```

### Client:
```
usage: client.py [-h] [-s] [-r] [-R] [-a <address>] [-p <port>] [-m <message>]
                 [--retrys [0-255]] [-nac] [-v]

SSPQ Client - Super Simple Python Queue Client

optional arguments:
  -h, --help            show this help message and exit
  -s, --send            Flag if you want to send data to the queue
  -r, --receive         Flag if you want to receive data from the queue
  -R, -dr, --dead-receive
                        Flag if you want to receive data from the dead letter
                        queue
  -a <address>, --address <address>
                        Set the server address to connect to.
  -p <port>, --port <port>
                        Set the port the server listens to
  -m <message>, --message <message>
                        Set the message to send
  --retrys [0-255]      Set the amount of retrys for failed messages. A value
                        of 255 is used to indicate infinite retrys.
  -nac, --no-auto-confirm
                        Disable auto confirm. WARNING this automatically
                        requeues the message since the conection is terminated
                        after the command finishes
  -v, --version         show program's version number and exit
```
