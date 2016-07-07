"""
    This module cotnains the MessageQueue class hierarchy.

    CONCEPT:
    - Message Queues are created with a class from Message class hierarchy as
    an argument, which sets what kind of messages will message queue contain

    INTERFACE:
    - get_message() - returns message instance from the queue
    - add_message(message) - adds the message instance from the queue. Must
    be an instance of Message class set before
"""

# NOTE - option to add thread-safety via mixins


class MessageQueue:
    """ Base of MessageQueue class hierarchy.

        NOTE - not thread-safe! Should not be used in situations in which
        race conditions may occur. """

    def __init__(self, msg_class=Message):
        if not issubclass(msg_class, Message):
            raise MessageQueueInitError("msg_class argument must be a class "
                                        "from Message class hierarchy")
        self._messages = []
        self.msg_class = msg_class

    # Interface methods
    def get_message(self):
        """ Returns message instance if there is one, removing it from the
            queue, else returns None. """
        if not self._messages:
            return None
        else:
            return self._messages.pop(0)

    def add_message(self, message):
        """ Attempts to append message to the internal queue.

            Raises error if message argument is not instance of the message
            class set during initialization """
        # NOTE - maybe check strictly, without allowing subclass' instances
        if not isinstance(message, self.msg_class):
            raise MessageQueueError("Can only add instances of %s class or its"
                                    " subclasses" % (self.msg_class))
        self._messages.append(message)

    def __len__(self):
        return len(self._messages)


class LockMessageQueue(MessageQueue):
    """ Subclass of MessageQueue which provides thread-safe access for usage
        in concurrent applications.

        Owns its private lock which is used during adding and removing messages
        from internal message list """

    def __init__(self, msg_class=Message):
        super().__init__(msg_class)
        self._lock = threading.Lock()

    # Interface methods
    def get_message(self):
        """ Retrieves the message using the internal threading.Lock object,
            therefore ensuring thread-safety! """
        with self._lock:
            if not self._messages:
                return None
            else:
                return self._messages.pop(0)

    def add_message(self, message):
        """ Adds the message instance using the internal threading.Lock object.

            If message is not instance of set message class, raises error """
        if not isinstance(message, self.msg_class):
            raise MessageQueueError("Can only add instances of %s"
                                    % self.msg_class)
        with self._lock:
            self._messages.append(message)
