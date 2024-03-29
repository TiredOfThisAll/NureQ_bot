import json
from urllib.error import HTTPError

import bot.server.handlers.constants as constants
from services.logging import LoggingLevel
from bot.server.router import callback_handler
from services.telegram.message_entities_builder import MessageEntitiesBuilder
from services.telegram.message_manager import MAX_MESSAGE_LENGTH


@callback_handler(constants.ButtonCallbackType.RESPONSIVE_UI_ADD_ME)
@callback_handler(constants.ButtonCallbackType.RESPONSIVE_UI_REMOVE_ME)
@callback_handler(constants.ButtonCallbackType.RESPONSIVE_UI_CROSS_OUT)
@callback_handler(constants.ButtonCallbackType.RESPONSIVE_UI_UNCROSS_OUT)
@callback_handler(constants.ButtonCallbackType.RESPONSIVE_UI_REFRESH)
def handle_generic_responsive_ui_callback(handler_context, update_context):
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
                f"Received callback ID {update_context.callback_query_type} "
                + "for a non-existent queue with ID {queue_id}"
            )
            notification_text = f"Очередь не найдена"
            return

        if update_context.callback_query_type \
                == constants.ButtonCallbackType.RESPONSIVE_UI_ADD_ME:
            error = handler_context.repository.add_me_to_queue(
                update_context.sender_user_info.id,
                update_context.sender_user_info.first_name,
                update_context.sender_user_info.last_name,
                update_context.sender_user_info.username,
                queue_id
            )
            name = update_context.sender_user_info.get_formatted_name()
            if error == "DUPLICATE_MEMBERS":
                notification_text \
                    = f"{name} уже состоит в данной очереди: {queue_name}"
                return
            success_notification_text \
                = f"{name} добавлен(а) в очередь: {queue_name}"
        elif update_context.callback_query_type \
                == constants.ButtonCallbackType.RESPONSIVE_UI_REMOVE_ME:
            success = handler_context.repository.remove_user_from_queue(
                user_info.id,
                queue_id
            )
            name = user_info.get_formatted_name()
            if not success:
                notification_text = f"{name} не состоит в очереди {queue_name}"
                return
            success_notification_text \
                = f"Участник {name} удален из очереди: {queue_name}"
        elif update_context.callback_query_type \
                == constants.ButtonCallbackType.RESPONSIVE_UI_CROSS_OUT:
            queue_member = handler_context \
                .repository.find_uncrossed_queue_member(queue_id)
            if queue_member is None:
                notification_text = "В данной очереди не осталось " \
                    + f"участников: {queue_name}"
                return

            handler_context.repository.cross_out_queue_member(
                queue_member.user_id,
                queue_id
            )
            name = queue_member.user_info.get_formatted_name()
            success_notification_text = f"Участник {name} вычеркнут из " \
                + f"очереди: {queue_name}"
        elif update_context.callback_query_type \
                == constants.ButtonCallbackType.RESPONSIVE_UI_UNCROSS_OUT:
            queue_member = handler_context.repository \
                .find_last_crossed_queue_member(queue_id)
            if queue_member is None:
                notification_text = "В данной очереди не осталось " \
                    + f"подходящих участников: {queue_name}"
                return

            handler_context.repository.uncross_out_the_queue_member(
                queue_member.user_id,
                queue_id
            )
            name = queue_member.user_info.get_formatted_name()
            success_notification_text = f"Участник {name} снова в очереди: " \
                + queue_name
        elif update_context.callback_query_type \
                == constants.ButtonCallbackType.RESPONSIVE_UI_REFRESH:
            success_notification_text = f"Очередь обновлена: {queue_name}"

        if update_context.callback_query_type \
                != constants.ButtonCallbackType.RESPONSIVE_UI_REFRESH:
            handler_context.repository.refresh_queues_last_time_updated_on(
                queue_id
            )

        queue_description_data, _error = generate_queue_description(
            handler_context.repository,
            queue_id
        )
        queue_description, entities, reply_markup = queue_description_data
        if update_context.is_message_unchanged(
            queue_description,
            entities,
            reply_markup
        ):
            notification_text = f"Очередь актуальна: {queue_name}"
            return
        try:
            handler_context.telegram_message_manager.edit_message_text(
                update_context.chat_id,
                update_context.message_id,
                queue_description,
                entities=entities,
                reply_markup=reply_markup
            )
        except HTTPError as http_error:
            # despite us checking for this above, if the message has changed,
            # while we were processing it, Telegram API will still throw this
            # 'message not modified' error, so we need an additional check here
            if http_error.code == 400:
                notification_text = f"Очередь актуальна: {queue_name}"
                return
            raise http_error

        notification_text = success_notification_text
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
                f"{index + 1}. {name}",
                type=type
            )
            # have to omit the final new line character, because otherwise
            # message diffing will start failing
            if index != len(queue_members) - 1:
                message_builder = message_builder.add_text("\n")
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
