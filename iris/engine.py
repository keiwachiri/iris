"""
    This module contains the Engine class hierarchy.

    CONCEPT:
    - Engine is responsible for main functionality of program - sending and
    receiving messages over the network
    - Intended to be simple to use, with a very clear interface, to be flexible
    and easy to plug in
    - Can be configured to work with different network protocols and
    programming concepts (OS Threads, OS Processes, asynchronously...)
    - Engine is provided endpoints which are set by the main application and
    which are used to send and receive message instances
    - It is provided with source of outgoing messages - that is - messages that
    are intended to be sent as well as the destination for incoming messages
    where new messages are to be stored. Both the destnation and source need to
    implement the appropriate interface, which is checked during the
    initialization of the engine

    IMPORTANT:
    - Engine's start needs to be invoked in a concurrent way!

    IMPLEMENTATIONS:
    - SequentialUDPEngine - single loop for sending and receiving
    - ThreadedUDPEngine - two threads, for sending and receiving
    - ProcessUDPEngine - two processes, for sending and receiving
    - AsyncUDPEngine - utilizes the asyncio event loop
    - SequentialTCPEngine - single loop for sending and receiving
    - ThreadedTCPEngine - two threads, for sending and receiving
    - ProcessTCPEngine - two processes, for sending and receiving
    - AsyncTCPEngine - utilizes the asyncio event loop
    - ThreadPoolTCPEngine - thread of pools for new connections

    INTERFACE:
    - __init__ - takes four parameters. Endpoint(s), incoming message queue
    and outgoing message queue
    - start - kicks of engine
    - stop - stops the engine. Can be restarted
    - shutdown - shuts down the resources it holds. Cannot be restarted
"""

import socket
import time
from threading import Thread

from iris.errors import (EngineError, EngineInitError, EngineEndpointError,
                         EngineMsgDestError, EngineMsgSourceError,
                         EngineStartError, EngineRunError, EngineFlagError)


class BaseEngine:
    """ The base class of Engine hierarchy, that offers only the structure,
        the base set of methods that form the API of the Engines and will be
        used by clients, it does not offer any implementation. """

    CREATED = 0
    RUNNING = 1
    STOPPED = 2
    SHUTDOWN = 3

    def __init__(self, listen_endp, send_endp, inc_dest, out_source):
        """ Responsible for ensuring that the arguments provided have the
            required interface and are of the same type """
        raise NotImplementedError

    def start(self):
        """ Start is a part of interface. Used to set the Engine running,
            performing its main functionality """
        raise NotImplementedError

    def stop(self):
        """ Stop is a part of interface. Used to stop the Engine that is
            already in the running state """
        raise NotImplementedError

    def shutdown(self):
        """ Shutdown is a part of interface. Used to close down any resources
            that Engine is using. After this, Engine can not be started """
        raise NotImplementedError


class BaseUDPEngine(BaseEngine):
    """ Base class of sub-hierarchy of Engines, which works on top of UDP
        as transport-layer protocol.

        Does not offer any concrete implementation, just adds methods
        required by protocol """

    def __init__(self, listen_endp, send_endp=None, inc_dest, out_source):
        """ Ensures that UDPEngine is set up properly to work on top of UDP.

            If listen endpoint is not set, it signals that Engine will be
            using a single endpoint(socket) for all activities.

            Checks for the interfaces of inc_dest and out_source arguments.

            If everything is ok, sets status to CREATED, it can raise
            EngineInitError """
        try:
            self._set_listen_endp(listen_endp)
            if send_endp:
                self._set_send_endp(send_endp)
            else:
                self._set_send_endp(listen_endp)
        except EngineEndpointError as e:
            raise EngineInitError("Failed in setting endpoints") from e
        try:
            self._set_incoming_msg_dest(inc_dest)
        except EngineMsgDestError as e:
            raise EngineInitError("Failed in setting destination for incoming"
                                  " messages") from e
        try:
            self._set_outgoing_msg_src(out_source)
        except EngineMsgSourceError as e:
            raise EngineInitError("Failed in setting source of outgoing "
                                  "messages") from e
        self.status = self.CREATED

    # Private methods called during __init__
    def _set_listen_endp(self, listen_endpoint):
        """ Checks whether the listen_endpoint is valid, sets it as the
            '_listen_endp' attribute if it is. """
        try:
            self._check_endpoint(listen_endpoint)
        except EngineEndpointError as e:
            raise e
        else:
            # NOTE - allows adding hook to perform custom configuration
            if hasattr(self, "_configure_listen_endpoint"):
                try:
                    self._configure_listen_endpoint(listen_endpoint)
                except EngineEndpointConfigureError as e:
                    raise e
            self._listen_endp = listen_endpoint

    def _set_send_endp(self, send_endpoint):
        """ Checks whether the provided argument is valid, sets it as
            `_send_endp` attribute if it is """
        try:
            self._check_endpoint(listen_endpoint)
        except EngineEndpointError as e:
            raise e
        else:
            self._send_endp = send_endpoint

    def _check_endpoint(self, endpoint):
        """ Checks whether the endpoint satisfies two requirements - has to
            be instance of socket.socket, and has to have type set to
            socket.SOCK_DGRAM. Raises error if not satisfied """
        if not isinstance(endpoint, socket.socket):
            raise EngineEndpointError("endpoint must be instance of socket!")
        if not endpoint.type == socket.SOCK_DGRAM:
            raise EngineEndpointError("endpoint must be socket of UDP type!")

    def _set_outgoing_message_source(self, out_source):
        """ Checks the interface required from outgoing message source, which
            is the method `get_message` that should return either a Message
            or None.

            If passed argument satisfies the interface, sets it as the
            `out_source` attribute, else raise EngineMsgSourceError """
        if hasattr(out_source, 'get_message'):
            self._out_source = out_source
        else:
            raise EngineMsgSourceError("Message source must provide the "
                                       "get_message method as interface")

    def _set_incoming_messages_destination(self, inc_dest):
        """ Checks the interface required from incoming message destination,
            which is the method `add_message` that adds arrived messages.

            If passed argument satisfies the interface, sets it as the
            '_inc_dest' attribute, else raise EngineMsgDestError """
        if hasattr(inc_dest, "add_message"):
            self._inc_dest = inc_dest
        else:
            raise EngineMsgDestError("Message destination must provide the "
                                     "add_message method as interface")
