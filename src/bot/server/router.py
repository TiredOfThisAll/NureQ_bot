import re

from bot.server.models.update_context import UpdateContext


registered_command_handlers = {}
registered_response_handlers = {}
registered_callback_handlers = {}

registered_default_command_handler = None
registered_default_response_handler = None
registered_default_callback_handler = None
registered_default_other_handler = None


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


def default_other_handler(function):
    global registered_default_other_handler
    registered_default_other_handler = function
    return function


def route(update_context, bot_username):
    if update_context.type == UpdateContext.Type.TEXT_MESSAGE:
        command = update_context.message_text

        # cut out the @BotName part if it is present
        command_first_word = command.split()[0]
        try:
            at_symbol_index = command_first_word.index(f"@{bot_username}")
        except ValueError:
            at_symbol_index = None
        if at_symbol_index is not None:
            command = command[:at_symbol_index] + command[len(command_first_word):]

        return get_or_match(
            registered_command_handlers,
            command,
            registered_default_command_handler
        )
    if update_context.type == UpdateContext.Type.RESPONSE:
        if update_context.responding_to_username != bot_username:
            # ignore replies to messages other than the bot's
            return noop_handler
        # try to find a matching response handler
        response_handler = get_or_match(
            registered_response_handlers,
            update_context.response_text
        )
        if response_handler is not None:
            return response_handler
        # otherwise, try to interpret it as a command
        full_bot_username = "@" + bot_username
        command = update_context.message_text
        if command.endswith(full_bot_username):
            command = command[:-len(full_bot_username)]
        return registered_command_handlers.get(
            command,
            # but still use default response handler as a fallback
            registered_default_response_handler
        )
    if update_context.type == UpdateContext.Type.CALLBACK_QUERY:
        return registered_callback_handlers.get(
            update_context.callback_query_type,
            registered_default_callback_handler
        )
    # only UpdateContext.Type.OTHER is left
    return registered_default_other_handler


def get_or_match(dictionary, target, fallback_value=None):
    for k, v in dictionary.items():
        # replace Python's format pattern with regex's "anything" pattern
        pattern = k.replace("{}", ".*")
        # pattern should represent the whole message, not just what text the
        # message starts with
        pattern = pattern + "$"
        if target == k or re.match(pattern, target):
            return v
    return fallback_value


def noop_handler(self, update_context):
    pass
