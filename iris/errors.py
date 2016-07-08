class MessageError(Exception):
    pass

class MessageInitError(MessageError):
    pass

class MessageEncodingError(MessageError):
    pass

class MessageDecodingError(MessageError):
    pass


class MessageQueueError(Exception):
    pass

class MessageQueueInitError(MessageQueueError):
    pass


class IrisError(Exception):
    pass

class IrisNetworkError(IrisError):
    pass

class IrisBindingError(IrisNetworkError):
    pass

class IrisSendingError(IrisError):
    pass


class EngineError(Exception):
    pass

class EngineInitError(EngineError):
    pass

class EngineEndpointError(EngineError):
    pass

class EngineMsgDestError(EngineError):
    pass

class EngineMsgSourceError(EngineError):
    pass

class EngineStartError(EngineError):
    pass

class EngineRunError(EngineError):
    pass

class EngineEndpointConfigureError(EngineError):
    pass

class EngineStopError(EngineError):
    pass

class EngineFlagError(EngineError):
    pass


class TranslatorError(Exception):
    pass

class TranslatorRegError(TranslatorError):
    pass

class TranslatorDeregError(TranslatorError):
    pass
