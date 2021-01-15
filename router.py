import json

registered_command_handlers = {}
registered_response_handlers = {}
registered_callback_handlers = {}

registered_default_command_handler = None
registered_default_response_handler = None
registered_default_callback_handler = None


def command_handler(command_name):
    def decorator(function):
        registered_command_handlers[command_name] = function

        def wrapper(*args, **kwargs):
            return function(*args, **kwargs)
        return wrapper
    return decorator


def response_handler(response_text):
    def decorator(function):
        registered_response_handlers[response_text] = function

        def wrapper(*args, **kwargs):
            return function(*args, **kwargs)
        return wrapper
    return decorator


def callback_handler(callback_type=None):
    def decorator(function):
        registered_callback_handlers[callback_type] = function

        def wrapper(*args, **kwargs):
            return function(*args, **kwargs)
        return wrapper
    return decorator


def default_command_handler(function):
    global registered_default_command_handler
    registered_default_command_handler = function

    def wrapper(*args, **kwargs):
        return function(*args, **kwargs)
    return wrapper


def default_response_handler(function):
    global registered_default_response_handler
    registered_default_response_handler = function

    def wrapper(*args, **kwargs):
        return function(*args, **kwargs)
    return wrapper


def default_callback_handler(function):
    global registered_default_callback_handler
    registered_default_callback_handler = function

    def wrapper(*args, **kwargs):
        return function(*args, **kwargs)
    return wrapper


def route(update):
    if "message" in update:
        message = update["message"]
        if "text" not in message:
            # unsupported message type
            message_text = ""
        else:
            message_text = message["text"]

        arguments = [message]

        # either it is a response to a bot's message
        if "reply_to_message" in message:
            response_text = message["reply_to_message"]["text"]
            if response_text not in registered_response_handlers:
                if registered_default_callback_handler is None:
                    return (None, None)
                return (registered_default_response_handler, arguments)
            return (registered_response_handlers[response_text], arguments)

        # or it is a normal text message with a command

        if message_text not in registered_command_handlers:
            if registered_default_command_handler is None:
                return (None, None)
            return (registered_default_command_handler, arguments)

        return (registered_command_handlers[message_text], arguments)

    if "callback_query" in update:
        callback_query = update["callback_query"]
        callback_query_data = json.loads(callback_query["data"])
        callback_query_type = callback_query_data["type"]

        arguments = [callback_query, callback_query_data]

        if callback_query_type not in registered_callback_handlers:
            if registered_default_callback_handler is None:
                return (None, None)
            return (registered_default_callback_handler, arguments)

        return (registered_callback_handlers[callback_query_type], arguments)

    return (None, None)
