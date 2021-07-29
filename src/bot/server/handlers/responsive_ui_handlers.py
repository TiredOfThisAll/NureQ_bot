import json

import bot.server.handlers.constants as constants
from bot.server.router import callback_handler
from services.telegram.message_entities_builder import MessageEntitiesBuilder
from services.telegram.message_manager import MAX_MESSAGE_LENGTH


@callback_handler(constants.ButtonCallbackType.RESPONSIVE_UI_ADD_ME)
def handle_responsive_ui_add_me_callback(handler_context, update_context):
    notification_text = None
    try:
        queue_id = update_context.callback_query_data["queue_id"]
        error = handler_context.repository.add_me_to_queue(
            update_context.sender_user_info.id,
            update_context.sender_user_info.first_name,
            update_context.sender_user_info.last_name,
            update_context.sender_user_info.username,
            queue_id
        )
        queue_name = handler_context.repository.get_queue_name_by_queue_id(
            queue_id
        )
        name = update_context.sender_user_info.get_formatted_name()
        if error == "DUPLICATE_MEMBERS":
            notification_text \
                = f"{name} уже состоит в данной очереди: {queue_name}"
            return
        if error == "NO_QUEUE":
            handler_context.logger.log(
                LoggingLevel.WARN,
                "Received a RESPONSIVE_UI_ADD_ME callback for a non-existent "
                + f"queue with ID {queue_id}"
            )
            notification_text = f"Очередь не найдена"
            return

        handler_context.repository.refresh_queues_last_time_updated_on(
            queue_id
        )

        queue_description_data, _error = generate_queue_description(
            handler_context.repository,
            queue_id
        )
        queue_description, entities, reply_markup = queue_description_data
        handler_context.telegram_message_manager.edit_message_text(
            update_context.chat_id,
            update_context.message_id,
            queue_description,
            entities=entities,
            reply_markup=reply_markup
        )

        notification_text = f"{name} добавлен(а) в очередь: {queue_name}"
    finally:
        handler_context.repository.commit()
        handler_context.telegram_message_manager.answer_callback_query(
            update_context.callback_query_id,
            text=notification_text
        )


@callback_handler(constants.ButtonCallbackType.RESPONSIVE_UI_REMOVE_ME)
def handle_responsive_ui_remove_me_callback(handler_context, update_context):
    notification_text = None
    try:
        user_info = update_context.sender_user_info
        queue_id = update_context.callback_query_data["queue_id"]
        queue_name = handler_context.repository.get_queue_name_by_queue_id(
            queue_id
        )
        if queue_name is None:
            handler_context.logger.log(
                LoggingLevel.WARN,
                "Received a RESPONSIVE_UI_REMOVE_ME callback for a "
                + f"non-existent queue with ID {queue_id}"
            )
            notification_text = f"Очередь не найдена"
            return

        success = handler_context.repository.remove_user_from_queue(
            user_info.id,
            queue_id
        )
        name = user_info.get_formatted_name()
        if not success:
            notification_text = f"{name} не состоит в очереди {queue_name}"
            return

        handler_context.repository.refresh_queues_last_time_updated_on(
            queue_id
        )

        queue_description_data, _error = generate_queue_description(
            handler_context.repository,
            queue_id
        )
        queue_description, entities, reply_markup = queue_description_data
        handler_context.telegram_message_manager.edit_message_text(
            update_context.chat_id,
            update_context.message_id,
            queue_description,
            entities=entities,
            reply_markup=reply_markup
        )

        notification_text = f"Участник {name} удален из очереди: {queue_name}"
    finally:
        handler_context.repository.commit()
        handler_context.telegram_message_manager.answer_callback_query(
            update_context.callback_query_id,
            text=notification_text
        )


@callback_handler(constants.ButtonCallbackType.RESPONSIVE_UI_CROSS_OUT)
def handle_responsive_ui_cross_out_callback(handler_context, update_context):
    notification_text = None
    try:
        queue_id = update_context.callback_query_data["queue_id"]
        queue_name = handler_context.repository.get_queue_name_by_queue_id(
            queue_id
        )
        if queue_name is None:
            handler_context.logger.log(
                LoggingLevel.WARN,
                "Received a RESPONSIVE_UI_CROSS_OUT callback for a "
                + f"non-existent queue with ID {queue_id}"
            )
            notification_text = f"Очередь не найдена"
            return

        queue_member = handler_context.repository.find_uncrossed_queue_member(
            queue_id
        )
        if queue_member is None:
            notification_text = "В данной очереди не осталось участников: " \
                + queue_name
            return

        handler_context.repository.cross_out_queue_member(
            queue_member.user_id,
            queue_id
        )
        handler_context.repository.refresh_queues_last_time_updated_on(
            queue_id
        )

        queue_description_data, _error = generate_queue_description(
            handler_context.repository,
            queue_id
        )
        queue_description, entities, reply_markup = queue_description_data
        handler_context.telegram_message_manager.edit_message_text(
            update_context.chat_id,
            update_context.message_id,
            queue_description,
            entities=entities,
            reply_markup=reply_markup
        )

        name = queue_member.user_info.get_formatted_name()
        notification_text = f"Участник {name} вычеркнут из очереди: " \
            + queue_name
    finally:
        handler_context.repository.commit()
        handler_context.telegram_message_manager.answer_callback_query(
            update_context.callback_query_id,
            text=notification_text
        )


def generate_queue_description(repository, queue_id):
    # check if queue exists and get its name, because we need to display it in
    # the response
    queue_name = repository.get_queue_name_by_queue_id(queue_id)
    if queue_name is None:
        return None, "QUEUE_NOT_FOUND"

    # get queue members for the body of the response
    queue_members = repository.get_queue_members_by_queue_id(queue_id)

    # generate the actual message with necessary styling, e.g. strike-throughs
    message_builder = MessageEntitiesBuilder(f"{queue_name}:\n")
    if len(queue_members) != 0:
        for index, queue_member in enumerate(queue_members):
            name = queue_member.user_info.get_formatted_name()
            type = "strikethrough" if queue_member.crossed else None
            message_builder = message_builder.add_text(
                f"{index + 1}. {name}\n",
                type=type
            )
    else:
        message_builder = message_builder.add_text("Очередь пуста")
    queue_description, entities = message_builder.build()

    # make sure to truncate both the message text and the message entities
    # down to the max allowed size for a Telegram message, because otherwise
    # Telegram API won't accept it
    truncated_queue_description = truncate(
        queue_description,
        MAX_MESSAGE_LENGTH,
        constants.DEFAULT_TRUNCATED_MESSAGE_PLACEHOLDER
    )
    truncated_entities = truncate_entities(
        entities,
        MAX_MESSAGE_LENGTH
    )
    reply_markup = generate_queue_actions_reply_markup(queue_id)

    return (
        truncated_queue_description,
        truncated_entities,
        reply_markup,
    ), None


def truncate(source, length, placeholder="..."):
    if len(source) > length:
        return source[:length - len(placeholder)] + placeholder
    return source


def truncate_entities(entities, length):
    return list(filter(
        lambda entity: entity["offset"] + entity["length"] <= length,
        entities
    ))


def generate_queue_actions_reply_markup(queue_id):
    return {
        "inline_keyboard": [
            [
                {
                    "text": "Добавить меня",
                    "callback_data": json.dumps({
                        "type": constants.ButtonCallbackType
                        .RESPONSIVE_UI_ADD_ME,
                        "queue_id": queue_id,
                    })
                },
                {
                    "text": "Убрать меня",
                    "callback_data": json.dumps({
                        "type": constants.ButtonCallbackType
                        .RESPONSIVE_UI_REMOVE_ME,
                        "queue_id": queue_id,
                    })
                },
            ],
            [
                {
                    "text": "Вычеркнуть",
                    "callback_data": json.dumps({
                        "type": constants.ButtonCallbackType
                        .RESPONSIVE_UI_CROSS_OUT,
                        "queue_id": queue_id,
                    })
                },
                {
                    "text": "Убрать вычеркивание",
                    "callback_data": json.dumps({
                        "type": constants.ButtonCallbackType
                        .RESPONSIVE_UI_UNCROSS_OUT,
                        "queue_id": queue_id,
                    })
                },
            ],
            [
                {
                    "text": "Обновить сообщение",
                    "callback_data": json.dumps({
                        "type": constants.ButtonCallbackType
                        .RESPONSIVE_UI_REFRESH,
                        "queue_id": queue_id,
                    })
                }
            ],
        ]
    }
