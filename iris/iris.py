"""
    This module contains Iris class hierarchy.

    Iris is the program which serves as a message transmitter, it is intended
    to be very flexible and implement many well-known or custom protocols,
    using different programming concepts, and that is easy to extends and
    customize.

    CONCEPT:
    - Message queues, for incoming and outgoing messages
    - Clean API which allows it to be embedded in more complex applications
    - Engine which is repsonsible for sending and receiving messages over wire
    - Translator which is responsible for encoding/decoding messages
    - Iris encapsulates and manages the internal socket/sockets which are
    utilized by Engine

    INTERFACE:
    - __init__() - the basic interface for creating new Iris instances,
    later to be replaced by factory functions
    - start() - used to start off the internal engine and kick off everything
    - stop() - used to stop everything
    - send_message() - adds message to be sent
    - receive_message() - gets new message
    - shutdown() - to shut down Iris instance, claiming back resources
"""

import socket
import time
import threading

from iris.message_queue import MessageQueue
from iris.message import Message
from iris.translator import Translator
from iris.engine import Engine
from iris.errors import (IrisBindingError, IrisSendingError, MessageInitError,
                         IrisError)
from iris import utils

class Iris:
    """ Base Iris class intended to be inherited and extended """

    UNBOUND = 0
    BOUND = 1

    CREATED = 11
    RUNNING = 12
    STOPPED = 13
    SHUTDOWN = 14

    def __init__(self):
        """ Calls the methods that initialize all functionalities of Iris and
            that different implementations can extend as they will """
        self._initialize_message_queues()
        self._initialize_endpoints()
        self._set_engine()
        self._set_translator()
        self.mode = self.UNBOUND
        self.status = self.CREATED

    def _initialize_message_queues(self):
        """ Sets four default message queues, pairs of incoming and outgoing,
            encoded and plain-text """
        self._inc_mq = MessageQueue()
        self._inc_mq_b = MessageQueue()
        self._out_mq = MessageQueue()
        self._out_mq_b = MessageQueue()

    def _initialize_endpoints():
        """ Sets one UDP socket """
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def _set_engine(self):
        """ Sets the desired Engine which will perform the operations of
            sending and receiving messages over the endpoint that we set """
        self.engine = Engine(endpoint=self._socket, inc_queue=self._inc_mq_b,
                             out_queue=self._out_mq_b)

    def _set_translator(self):
        """ Sets basic translator and registers the basic queues """
        self.translator = Translator()
        self.translator.register_translation(self._out_mq, self.out_mq_b,
                                             Translator.ENCODING, "Encoding")
        self.translator.register_translation(self._inc_mq_b, self._inc_mq,
                                             Translator.DECODING, "Decoding")


    # API methods
    def send_message(self, payload, host, port):
        """ Client uses this method of Iris to send message to desired host
            and port, over the internet, using the supported protocols
            specified during the instantiation.

            Address is checked to be valid by `is_valid_address` functions
            from utils module.

            Iris attempts to create the Message instance from the payload,
            and add it to the outgoing MessageQueue """
        if not utils.is_valid_address(host, port):
            raise IrisSendingError("Given invalid address - host: %s"
                                   " port: %d" % (host, port))
        try:
            # TODO - add Message Class as attribute - maybe register it
            msg = Message(payload, host, port)
        except MessageInitError as e:
            raise IrisSendingError("Failed to create message with "
                                   "payload: %s" % payload) from e
        else:
            self._inc_mq.add_message(msg)

    def receive_message(self):
        """ Client usees this method of Iris to receive incoming messages
            over the internet, via supported protocols specified during
            the instantiation.

            Different options - could return None, block or something third
            like some variation of Future etc.

            Message is returned as a tuple (payload, host, port) """
        # TODO - figure out best way to add blocking/nonblocking
        # For now - only non-blocking version which returns None
        msg = self._inc_mq.get_message()
        if msg:
            msg = msg.payload, msg.address[0], msg.address[1]
        return msg

    def bind(self, interface, port):
        """ Used to bind the internal socket, if we want its address to be
            well-known and not left to be set randomly by OS.

            Sets mode to BOUND
            NOTE - right now can only be set once. """
        if not self.mode == self.UNBOUND:
            raise IrisBindingError("Can bind only when mode is UNBOUND")
        if not is_valid_address(interface, port):
            raise IrisBindingError("Address not valid - interface: %s"
                                   " port: %d" % (interface, port))
        addr = interface, port
        try:
            self._socket.bind(addr)
        except OSError as e:
            raise IrisBindingError("Failed to bind to ", str(addr)) from e
        else:
            self.mode = self.BOUND

    def start(self):
        """ Starts everything, and sets status to 'RUNNING' """
        if not(self.status == self.CREATED or self.status == self.STOPPED):
            raise IrisError("Cannot start from the current status")
        self.status = self.RUNNING
        self._run_flag = True
        self.engine.start()
        self.translator.start()
        run_thread = threading.Thread(target=self._run, name='Iris-Run')
        run_thread.start()

    def _run(self):
        """ Basic sequential implementation. While status is 'RUNNING', it
            loops and calls the appropriate methods """
        if not self._run_flag:
            raise IrisError("Can not start running if flag is not set")
        while self._run_flag:
            time.sleep(0.001)
        else:
            self.status = self.STOPPED

    def stop(self):
        """ Stops everything, can only be called while status is 'RUNNING' """
        if not self.status == self.RUNNING:
            raise IrisError("Cannto stop if status is not RUNNING")
        self.engine.stop()
        while not self.engine.status == Engine.STOPPED:
            time.sleep(0.001)
        self.translator.stop()
        while not self.translator.status == Translator.STOPPED:
            time.sleep(0.001)
        self._run_flag = False

    def shutdown(self):
        """ One of the interface methods, reclaims resources """
        self.close()
        self.status = self.SHUTDOWN

    def close(self):
        self._socket.close()
