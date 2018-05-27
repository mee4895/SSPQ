# SSPQ Protocol Documentation

The SSPQ protocol is based on a tcp session. After establishing the connection the client is expected to tell the server what todo.

A SEND-package can be send anytime and is not acknowledged by the server to be inline with the send and forget pattern. It is the only package send with a payload, all others are usually send with a empty payload.

A RECEIVE-package should only be send if the client is not working on a package and has confirmed it. After the RECEIVE-package is send the server is going to answer with a SEND-package with a message payload as soon as a message is available from the queue. The server may answer with a NO_RECEIVE-package to indicate to the client that there will be no message comming. After the message is processed the client should send a CONFIRM-package to remove the package from the queue. If the connection is terminated befor a CONFIRM-package is send the server is, depending on the retry counter of the message, going to requeue it.

A DEAD_RECEIVE-package behaves the same as the RECEIVE-package with the only difference that the message is fetched from the dead-letter queue and not from the normal messaging queue. The server expects the same CONFIRM-package but always requeues the message on a sudden disconnect.


## Package Structure

| Byte | Size | Usage                                   |
|------|------|-----------------------------------------|
| 0-1  | 2    | Magicnumber 0x5599                      |
| 2    | 1    | Package Type (see Package Type section) |
| 3    | 1    | Retry Counter                           |
| 4-7  | 4    | Payload Size                            |
| 8-n  | -    | Payload                                 |


## Package Types

| Name         | Byte | Usage                                                   |
|--------------|------|---------------------------------------------------------|
| SEND         | 0x5e | Used to send a message to the server or client          |
| RECEIVE      | 0xec | Used to request a message from the server               |
| CONFIRM      | 0xc0 | Used to confirm a message and remove it from it's queue |
| DEAD_RECEIVE | 0xde | Used to request a message from the dead letter queue    |
| NO_RECEIVE   | 0x0e | Used by the server to decline a message request         |
|              |      |                                                         |
| OTHER        | 0xff | Internal format for unknown packages                    |
