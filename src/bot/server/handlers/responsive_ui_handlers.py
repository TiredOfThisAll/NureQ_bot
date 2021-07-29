import json

import bot.server.handlers.constants as constants
from services.telegram.message_entities_builder import MessageEntitiesBuilder
from services.telegram.message_manager import MAX_MESSAGE_LENGTH


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
                    })
                },
                {
                    "text": "Убрать меня",
                    "callback_data": json.dumps({
                        "type": constants.ButtonCallbackType
                        .RESPONSIVE_UI_REMOVE_ME,
                    })
                },
            ],
            [
                {
                    "text": "Вычеркнуть",
                    "callback_data": json.dumps({
                        "type": constants.ButtonCallbackType
                        .RESPONSIVE_UI_CROSS_OUT,
                    })
                },
                {
                    "text": "Убрать вычеркивание",
                    "callback_data": json.dumps({
                        "type": constants.ButtonCallbackType
                        .RESPONSIVE_UI_UNCROSS_OUT,
                    })
                },
            ],
            [
                {
                    "text": "Обновить сообщение",
                    "callback_data": json.dumps({
                        "type": constants.ButtonCallbackType
                        .RESPONSIVE_UI_REFRESH
                    })
                }
            ],
        ]
    }
