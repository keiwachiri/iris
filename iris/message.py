"""
    Module which contains the Message class heirarchy.

    CONCEPT:
    - Message classes represent the actual types of messages that are being
    transferred over the network by Iris
    - each Message class has two modes - binary and nonbinary
    - each Message class has two posses two methods that will enable the
    encoding and decoding from these two modes
"""

from iris.errors import (MessageInitError, MessageEncodingError,
                         MessageDecodingError)
from iris import utils


class Message:
    """ Base class of Message class hierarchy.

        Contains basic text strings as payload, with staticmethods
        offering basic encoding and decoding of the payload """

    NONBINARY = 0
    BINARY = 1

    PAYLOAD_SIZE = 1500

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

    def __init__(self, payload, host, port):
        """ Initializes the Message object. Based on the type of payload,
            sets mode to BINARY or NONBINARY. """
        if not utils.is_valid_address(host, port):
            raise MessageInitError("Can not initialize Message with host: %s"
                                   " and port: %d" % (host, port))
        if not payload:
            raise MessageInitError("Can not initialize Message with payload %s"
                                   % payload)
        if isinstance(payload, bytes):
            self.mode = Message.BINARY
        elif isinstance(payload, str):
            self.mode = Message.NONBINARY
        else:
            raise MessageInitError("Can not initialize Message with payload of"
                                   "type %s" % str(type(payload)))
        self.payload = payload
        self.address = host, port
