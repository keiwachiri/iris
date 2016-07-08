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


class SequentialUDPEngine(BaseUDPEngine):
    """ Sequential implementation of the UDPEngine. This is a very inefficient
        class, should not be used in any serious application, but purely
        for educational/fun purposes """

    def start(self):
        """ Responsible to set the SequentialUDPEngine running.
            Sets the _run_flag and invokes the run operation.

            Can only be called from CREATED or STOPPED state. """
        if self.status in (self.CREATED, self.STOPPED):
            self._run_flag = True
            self._run()
        else:
            raise EngineStartError("Can only be started when status is set to"
                                   " CREATED or STOPPED")

    def _run(self):
        """ Method responsible for performing the main functionaity of the
            application, that is, for performing the sending and receiving of
            messages.

            Can only be invoked when the _rcv_flag is set to True. Sets the
            status to RUNNING, and loops while _rcv_flag is True. After being
            done sets the status to STOPPED """
        if self._run_flag:
            self.status = self.RUNNING
            while self._run_flag:
                self._send()
                self._receive()
            else:
                self.status = self.STOPPED
        else:
            raise EngineRunError("Cannot call _run method without _run_flag")

    def stop(self):
        """ Uses _run_flag to signal _run to stop running.

            Waits until the status is set to STOPPED and then returns """
        if self.status == self.RUNNING:
            self._run_flag = False
            while not self.status == self.STOPPED:
                time.sleep(0.001)
        else:
            raise EngineStopError("Cannot invoke stop when status not RUNNING")

    def shutdown(self):
        """ If status is STOPPED or CREATED, it proceeds to shut down otherwise
            it invokes the stop method first """
        if self.status == self.RUNNING:
            self.stop()
        if self.status in (self.STOPPED, self.CREATED):
            self._listen_endp.close()
            self._send_endp.close()
            self.status = self.SHUTDOWN
        else:
            raise EngineShutdownError("Invalid status: Engine Status %s"
                                      % self.status)

    def _configure_listen_endpoint(self, listen_endpoint):
        """ Required so that the receiving doesn't stop the entire Engine """
        listen_endpoint.setblocking(False)

    # sending-related methods
    def _send(self):
        msg = self._out_source.get_message()
        if msg:
            try:
                self._send_message(msg)
            except EngineSendError as e:
                raise e  # TODO - log here

    def _send_message(self, message):
        try:
            self._send_payload(payload=msg.payload, address=msg.address)
        except Exception as e:
            raise e

    def _send_payload(self, payload, address):
        try:
            self._send_endp.sendto(payload, address)
        except socket.gaierror as e:
            raise EngineSendError("Cannot find such address: ",
                                  str(address)) from e
        except OSError as e:
            raise EngineSendError("Failed to send message payload: %s"
                                  % payload) from e

    # receiving-related methods
    def _receive(self):
        message = self._receive_message()
        if message:
            self._inc_dest.add_message(new_message)
        else:
            pass # TODO - log

    def _receive_message(self):
        payload, addr = self._receive_data()
        if payload:
            try:
                new_message = self._inc_dest.msg_class(payload=payload,
                                                       addr=addr)
            except MessageInitError as e:
                pass # TODO - log here
            else:
                return new_message

    def _receive_data(self):
        try:
            payload, addr = self._listen_endp.recvfrom(1500) # TODO - msg size
        except BlockingIOError:
            return (None, None)


class ThreadedUDPEngine(BaseUDPEngine):
    """ Implementation of UDPEngine which works by creating separate threads
        for sending and receiving functionalities """

    def _run(self):
        """ Run starts two separate threads for sending and receiving of
            messages and loops until the run_flag is set to False, when it
            waits for sending and receiving to finish """
        if self._run_flag:
            rcv_thread = Thread(target=self._receiving,
                                name='Engine-Receiving')
            send_thread = Thread(target=self._sending,
                                 name='Engine-Sending')
            self._send_flag = True
            self._rcv_flag = True
            send_thread.start()
            rcv_thread.start()
            self.status = self.RUNNING
            while self._run_flag:
                time.sleep(0.001)
            else:
                self._send_flag = False
                self._rcv_flag = False
                send_thread.join()
                rcv_thread.join()
                self.status = self.STOPPED
        else:
            raise EngineRunError("Cannot call _run_method without _run_flag")

    def _receiving(self):
        """ Communicates with outer world via _rcv_flag. Calls the _receive
            until flag is set to False, then it exits """
        if self._rcv_flag:
            while self._rcv_flag:
                self._receive()
        else:
            raise EngineFlagError("_receiving can only be called when the "
                                  "_rcv_flag is set to True")

    def _sending(self):
        """ Communicates with outer world via _send_flag. Calls the _send
            until flag is set to False, then it exits. """
        if self._send_flag:
            while self._send_flag:
                self._send()
        else:
            raise EngineFlagError("_sending can only be called when the "
                                  "_send_flag is set to True beforehand")
