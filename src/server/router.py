import re

from server.models.update_context import UpdateContext


registered_command_handlers = {}
registered_response_handlers = {}
registered_callback_handlers = {}

registered_default_command_handler = None
registered_default_response_handler = None
registered_default_callback_handler = None


def command_handler(command_name):
    def decorator(function):
        registered_command_handlers[command_name] = function
        return function
    return decorator


def response_handler(response_text):
    def decorator(function):
        registered_response_handlers[response_text] = function
        return function
    return decorator


def callback_handler(callback_type=None):
    def decorator(function):
        registered_callback_handlers[callback_type] = function
        return function
    return decorator


def default_command_handler(function):
    global registered_default_command_handler
    registered_default_command_handler = function
    return function


def default_response_handler(function):
    global registered_default_response_handler
    registered_default_response_handler = function
    return function


def default_callback_handler(function):
    global registered_default_callback_handler
    registered_default_callback_handler = function
    return function


def route(update_context):
    if update_context.type == UpdateContext.Type.MESSAGE:
        # either it is a response to a bot's message
        if update_context.is_reply:
            if update_context.responding_to_username != "some_one_new_test_bot":
                # ignore replies to messages other than the bot's
                return noop_handler
            return get_or_match(
                registered_response_handlers,
                update_context.response_text,
                registered_default_response_handler
            )
        # or it is a normal text message with a command
        return registered_command_handlers.get(
            update_context.message_text,
            registered_default_command_handler
        )
    if update_context.type == UpdateContext.Type.CALLBACK_QUERY:
        return registered_callback_handlers.get(
            update_context.callback_query_type,
            registered_default_callback_handler
        )


def get_or_match(dictionary, target, fallback_value):
    for k, v in dictionary.items():
        if target == k or re.match(k.replace("{}", ".*"), target):
            return v
    return None


def noop_handler(self, update_context):
    pass
