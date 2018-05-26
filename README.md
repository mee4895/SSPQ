# SSPQ - The super simple python queue
> A quick messaging queue everywhere, there is python.


## Motivation:
The motivation for this project is to have a very simple light weight queue server which is easy to package with your application. This allows for quick and easy testing and development setups without the need for an installed full-blown messaging server.


## Prerequesits:
- python: >3.6 (should work with 3.5, but this is developed with and for 3.6)


## Usage:

### Server:
```
usage: server.py [-h] [--host <host>] [-p <port>] [-ll <log-level>] [-v]

SSPQ Server - Super Simple Python Queue Server

optional arguments:
  -h, --help            show this help message and exit
  --host <host>         Set the host address. Juse 0.0.0.0 to make the server
                        public
  -p <port>, --port <port>
                        Set the port the server listens to
  -ll <log-level>, --loglevel <log-level>
                        Set the appropriate log level for the output on
                        stdout. Possible values are: [ fail | warn | info |
                        dbug ]
  -v, --version         show program's version number and exit
```

### Client:
```
usage: client.py [-h] [-s] [-r] [-a <host>] [-p <port>] [-m <message>] [-v]

SSPQ Client - Super Simple Python Queue Client

optional arguments:
  -h, --help            show this help message and exit
  -s, --send            Flag if you want to send data to the queue
  -r, --receive         Flag if you want to receive data from the queue
  -a <host>, --address <host>
                        Set the server address to connect to.
  -p <port>, --port <port>
                        Set the port the server listens to
  -m <message>, --message <message>
                        Set the message to send
  -v, --version         show program's version number and exit

```
