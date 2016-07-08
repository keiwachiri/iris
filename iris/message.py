"""
    Module which contains the Message class heirarchy.

    CONCEPT:
    - Message classes represent the actual types of messages that are being
    transferred over the network by Iris
    - each Message class has two modes - binary and nonbinary
    - each Message class has two posses two methods that will enable the
    encoding and decoding from these two modes
    - Message classes have defined maximum sizes of messages

    FUTURE:
    - add persisting stuff - possibly as a mixing, messages have to be
    persisted for state-saving purposes
    - add id stuff - for identification of messages
"""

from iris.errors import (MessageInitError, MessageEncodingError,
                         MessageDecodingError)
from iris import utils


class BaseMessage:
    """ Base class of Message class hierarchy.

        Gives the overall skeleton which has to be inherited. """

    NONBINARY = 0
    BINARY = 1


    @staticmethod
    def to_binary(message):
        raise NotImplementedError

    @staticmethod
    def from_binary(message):
        raise NotImplementedError

    def __init__(self, payload, host, port):
        if not utils.is_valid_address(host, port):
            raise MessageInitError("Invalid address %s:%s was provided"
                                   % (str(host, str(port))))
        if not payload:
            raise MessageInitError("Cannot initialize without payload!")
        if type(payload) == bytes:
            self._init_binary(payload, host, port)
        else:
            self._init_nonbinary(payload, host, port)

    def _init_binary(self, payload, host, port):
        raise NotImplementedError

    def _init_nonbinary(self, payload, host, port):
        raise NotImplementedError


class TextMessage:
    """ Base class of Message class sub-hierarchy that uses text payload.

        Contains basic text strings as payload, with static methods
        offering basic encoding and decoding of the payload """

    PAYLOAD_SIZE_BINARY = 1500


    @staticmethod
    def to_binary(message):
        """ Responsible for encoding the message into BINARY mode, from
            NONBINARY, in order to get it ready for transmission.

            Can only be called with message in NONBINARY mode """
        if message.mode == Message.NONBINARY:
            try:
                # TODO - add encoding as class parameter
                message.payload = message.payload.encode('UTF-8')
            except UnicodeEncodeError as e:
                raise MessageEncodingError("Failed to encode the payload: %s"
                                           % message.payload) from e
            else:
                message.mode = Message.BINARY
                return message
        else:
            raise MessageEncodingError("Message must be in NONBINARY mode")

    @staticmethod
    def from_binary(message):
        """ Responsible for decoding the message into NONBINARY mode, from
            BINARY, in order to get it ready for consumption by client.

            Can only be called with message in BINARY mode """
        if message.mode == Message.BINARY:
            try:
                message.payload = message.payload.decode("UTF-8")
            except UnicodeDecodeError as e:
                raise MessageDecodingError("Failed to decode the payload: %s"
                                           % message.payload) from e
            else:
                message.mode = Message.NONBINARY
                return message
        else:
            raise MessageDecodingError("Message must be in BINARY mode")

    def _init_binary(self, payload, host, port):
        self.payload = payload
        self.address = host, port
        self.mode = self.BINARY

    def _init_nonbinary(self, payload, host, port):
        if type(payload) == str:
            self.payload = payload
            self.address = host, port
            self.mode = self.NONBINARY
        else:
            raise MessageInitError("Nonbinary TextMessages must have payload"
                                   " of str type not: %s" % str(type(payload)))
