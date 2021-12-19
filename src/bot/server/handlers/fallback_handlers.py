from bot.server.router import default_callback_handler, \
    default_command_handler, default_response_handler, default_other_handler
from services.logging import LoggingLevel


@default_callback_handler
def handle_unknown_callback(handler_context, update_context):
    callback_type = update_context.callback_query_type
    handler_context.logger.log(
        LoggingLevel.ERROR,
        f"Received an unknown callback query type: {callback_type}"
    )
    if update_context.chat_type == "private":
        handler_context.telegram_message_manager.send_message(
            update_context.chat_id,
            "Неизвестная команда"
        )
    handler_context.telegram_message_manager.answer_callback_query(
        update_context.callback_query_id
    )


@default_command_handler
def handle_unknown_response(handler_context, update_context):
    handler_context.logger.log(
        LoggingLevel.WARN,
        f"Received an invalid command: {update_context.update}"
    )
    if update_context.chat_type == "private":
        handler_context.telegram_message_manager.send_message(
            update_context.chat_id,
            "Неизвестная команда"
        )


@default_response_handler
def handle_unknown_response(handler_context, update_context):
    if update_context.chat_type == "private":
        handler_context.telegram_message_manager.send_message(
            update_context.chat_id,
            "Неизвестная команда"
        )
    handler_context.logger.log(
        LoggingLevel.WARN,
        f"Received an invalid response: {update_context.update}"
    )


@default_other_handler
def handle_other_updates(handler_context, update_context):
    handler_context.logger.log(
        LoggingLevel.WARN,
        f"Received an update of type 'other': {update_context.update}"
    )


def handle_error_while_processing_update(handler_context, update_context):
    try:
        handler_context.telegram_message_manager.send_message(
            update_context.chat_id,
            "Ошибка"
        )
    except Exception:
        pass
