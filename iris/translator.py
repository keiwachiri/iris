"""
    Contains Translator class hierarchy.

    CONCEPT:
    - Translator is responsible for ensuring that outgoing messages are being
    properly encoded, and that the incoming messages are being decoded
    - It is given a pairs of Message Queues, one which serves as a source, one
    which serves as a destination
    - Translator performs the desired operation on the messages from input
    queue and adds them to the output queue
    - Translator may handle many pairs of queues, they are 'registered' after
    his creation

    INTERFACE:
    * __init__ sets up the Translator
    * register_operation(src_queue, dest_queue, operation, op_name) - used
    to register the encoding/decoding that we want performed on the two given
    queues under the name that is passed as argument
    * deregister_operation(op_name) - removes the encoding/decoding that
    is registered under the name
    * start - sets everything running
    * stop - stops everything
"""

import threading

from iris.errors import (TranslatorError, TranslatorRegError,
                         MessageDecodingError, TranslatorDeregError,
                         MessageEncodingError)


class Translator:
    """ Base implementation of Translator """

    CREATED = 10
    RUNNING = 11
    STOPPED = 12


    def __init__(self):
        self.operations = {}
        self.status = self.CREATED

    def register_operation(self, input, output, operation, op_key):
        """ Input and output are required to satisfy the desired interface,
            and must have their Message class attributes set as equal. """
        try:
            self._check_interface(input, attr="get_message")
            self._check_interface(output, attr="add_message")
            self._check_interface(operation, type_is=function)
            self._check_operation_key(op_key)
        except TranslatorInputError, TranslatorOutputError as e:
            raise TranslatorRegError("Failed to register translation") from e
        except TranslatorOperationError as e:
            raise TranslatorRegError("Failed to register translation with"
                                     " provided operation") from e
        except TranslatorOperationKeyError as e:
            raise TranslatorRegError("Failed to register translation with the "
                                "operation key provided: %s" % op_key) from e
        else:
            self._add_operation(input, output, operation, op_key)

    def _check_interface(self, object, attr=None, type_is=None):
        if attr:
            if not hasattr(object, attr):
                raise TranslatorInterfaceError("Object must provide attribute"
                                               " %s for translator" % attr)
        if type_is:
            if not type(object) == type_is:
                raise TranslatorInterfaceError("Object must be of type %s "
                                               "for translator" % str(type_is))

    def _check_operation_key(self, op_key):
        if not hasattr(op_key, "__hash__"):
            raise OperationKeyError("OpKey must provide `__hash__` method")
        if not hasattr(op_key, "__eq__"):
            raise OperationKeyError("OpKey must provide '__eq__' method")

    def _add_operation(self, input, output, operation, op_key):
        if not op_key in self.operations:
            self.operations[op_key] = (input, output, operation)
        else:
            raise OperationAddError("Operation %s already registerd under the"
                                    " same key" % str(self.operations[op_key]))

    def deregister_operation(self, op_key):
        if op_name in self.operations:
            self.operations.pop(op_name)
        else:
            raise TranslatorDeregError("Operation Key %s not registered"
                                       % str(op_key))

    def start(self):
        """ Responsible for starting internal _run() that runs in a single
            thread, setting the running flag before it to True """
        if self.status in (self.CREATED, self.STOPPED):
            self._run_flag = True
            self._run()
        else:
            raise TranslatorStartError("Start must be called from CREATED or "
                                      "STOPPED status!")

    def _run(self):
        """ Sequentially loops over the registered actions and invokes them """
        if self._run_flag:
            self.status = self.RUNNING
            while self._run_flag:
                for op in self.operations:
                    try:
                        message = self.operations[op][0].get_message()
                        message_processed = self.operations[op][2]()
                        self.operations[op][1].add_message(message_processed)
                    except MessageError as e:
                        raise e # TODO
            else:
                self.status = self.STOPPED
        else:
            raise TranslatorRunError("Run cannot be called without _run_flag")

    def stop(self):
        """ If status is RUNNING, sets the running flag to False """
        if self.status == self.RUNNING:
            self._run_flag = False
            while not self.status == self.STOPPED:
                time.sleep(0.001)
        else:
            raise TranslatorStopError("Stop cannot be called when not RUNNING")
