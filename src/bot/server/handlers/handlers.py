import math
import json
import random

import bot.server.handlers.constants as constants
from bot.server.router import command_handler, response_handler, \
    callback_handler, default_callback_handler, default_command_handler, \
    default_response_handler, default_other_handler
from bot.server.models.update_context import UpdateContext
from services.logging import LoggingLevel
from services.telegram.message_entities_builder import MessageEntitiesBuilder
from services.telegram.message_manager import MAX_MESSAGE_LENGTH


@command_handler("/start")
@command_handler("/start@NureQ_bot")
def handle_start_command(handler_context, update_context):
    handler_context.telegram_message_manager.send_message(
        update_context.chat_id,
        "Йоу"
    )


@command_handler("/newqueue")
def handle_new_queue_command(handler_context, update_context):
    handler_context.telegram_message_manager.send_message(
        update_context.chat_id,
        constants.NEW_QUEUE_COMMAND_RESPONSE_TEXT,
        reply_markup={"force_reply": True, "selective": True},
        reply_to_message_id=update_context.message_id
    )


@command_handler("/showqueue")
def handle_show_queue_command(handler_context, update_context):
    handle_generic_queue_command(
        handler_context,
        update_context,
        constants.ButtonCallbackType.SHOW_QUEUE,
        "Выберите очередь, которую хотите посмотреть."
    )


@command_handler("/crossout")
def handle_cross_out_command(handler_context, update_context):
    handle_generic_queue_command(
        handler_context,
        update_context,
        constants.ButtonCallbackType.CROSS_OUT,
        "Выберите очередь, из которой необходимо вычеркнуть участника"
    )


@command_handler("/uncrossout")
def handle_uncross_out_command(handler_context, update_context):
    handle_generic_queue_command(
        handler_context,
        update_context,
        constants.ButtonCallbackType.UNCROSS_OUT,
        "Выберите очередь, в которую необходимо вернуть участника"
    )


@command_handler("/addme")
def handle_add_me_command(handler_context, update_context):
    handle_generic_queue_command(
        handler_context,
        update_context,
        constants.ButtonCallbackType.ADD_ME,
        "Выберите очередь, в которую хотите добавиться."
    )


@command_handler("/removeme")
def handle_remove_me_command(handler_context, update_context):
    handle_generic_queue_command(
        handler_context,
        update_context,
        constants.ButtonCallbackType.REMOVE_ME,
        "Выберите очередь, которую хотите покинуть."
    )


@response_handler(constants.NEW_QUEUE_COMMAND_RESPONSE_TEXT)
@response_handler(constants.QUEUE_NAME_ONLY_TEXT_RESPONSE_TEXT)
@response_handler(constants.QUEUE_NAME_TOO_LONG_RESPONSE_TEXT)
def handle_new_queue_response(handler_context, update_context):
    if update_context.response_type != UpdateContext.Type.TEXT_MESSAGE:
        handler_context.logger.log(
            LoggingLevel.WARN,
            "Received a non-text response to /newqueue command: "
            + str(update_context.update)
        )
        handler_context.telegram_message_manager.send_message(
            update_context.chat_id,
            constants.QUEUE_NAME_ONLY_TEXT_RESPONSE_TEXT,
            reply_markup={"force_reply": True, "selective": True},
            reply_to_message_id=update_context.message_id
        )
        return
    queue_name = update_context.message_text
    queue_name_limit = handler_context.configuration.queue_name_limit
    if len(queue_name) > queue_name_limit:
        handler_context.logger.log(
            LoggingLevel.WARN,
            "Received a response to /newqueue command that exceeds the "
            + f"configured limit of {queue_name_limit} "
            + f"UTF-8 characters: {queue_name}"
        )
        handler_context.telegram_message_manager.send_message(
            update_context.chat_id,
            constants.QUEUE_NAME_TOO_LONG_RESPONSE_TEXT.format(
                queue_name_limit
            ),
            reply_markup={"force_reply": True, "selective": True},
            reply_to_message_id=update_context.message_id
        )
        return
    error = handler_context.repository.create_queue(queue_name)
    handler_context.repository.commit()
    if error == "QUEUE_NAME_DUPLICATE":
        handler_context.telegram_message_manager.send_message(
            update_context.chat_id,
            f"Очередь с именем {queue_name} уже существует"
        )
        return

    handler_context.telegram_message_manager.send_message(
        update_context.chat_id,
        f"Создана новая очередь: {queue_name}"
    )


@callback_handler(constants.ButtonCallbackType.ADD_ME)
def handle_add_me_callback(handler_context, update_context):
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
            handler_context.telegram_message_manager.send_message(
                update_context.chat_id,
                f"{name} уже состоит в данной очереди: {queue_name}"
            )
            return
        if error == "NO_QUEUE":
            handler_context.logger.log(
                LoggingLevel.WARN,
                "Received an /addme request for a non-existent queue "
                + f"with ID {queue_id}"
            )
            handler_context.telegram_message_manager.send_message(
                update_context.chat_id,
                "Данной очереди не существует: " + queue_name
            )
            return
        handler_context.repository.refresh_queues_last_time_updated_on(
            queue_id
        )
        handler_context.telegram_message_manager.send_message(
            update_context.chat_id,
            f"{name} добавлен(а) в очередь: {queue_name}"
        )
    finally:
        handler_context.repository.commit()
        handler_context.telegram_message_manager.answer_callback_query(
            update_context.callback_query_id
        )


@callback_handler(constants.ButtonCallbackType.CROSS_OUT)
def handle_cross_out_callback(handler_context, update_context):
    try:
        queue_id = update_context.callback_query_data["queue_id"]
        queue_member = handler_context.repository.find_uncrossed_queue_member(
            queue_id
        )
        queue_name = handler_context.repository.get_queue_name_by_queue_id(
            queue_id
        )

        if queue_member is None:
            handler_context.telegram_message_manager.send_message(
                update_context.chat_id,
                f"В данной очереди не осталось участников: {queue_name}"
            )
            return

        handler_context.repository.cross_out_queue_member(
            queue_member.user_id,
            queue_id
        )
        handler_context.repository.refresh_queues_last_time_updated_on(
            queue_id
        )
        handler_context.repository.commit()

        name = queue_member.user_info.get_formatted_name()
        handler_context.telegram_message_manager.send_message(
            update_context.chat_id,
            f"Участник {name} вычеркнут из очереди: {queue_name}"
        )
    finally:
        handler_context.telegram_message_manager.answer_callback_query(
            update_context.callback_query_id
        )


@callback_handler(constants.ButtonCallbackType.UNCROSS_OUT)
def handle_uncross_out_callback(handler_context, update_context):
    try:
        queue_id = update_context.callback_query_data["queue_id"]
        queue_member = handler_context.repository \
            .find_last_crossed_queue_member(queue_id)
        queue_name = handler_context.repository.get_queue_name_by_queue_id(
            queue_id
        )

        if queue_member is None:
            handler_context.telegram_message_manager.send_message(
                update_context.chat_id,
                "В данной очереди не осталось подходящих участников: "
                + queue_name
            )
            return

        handler_context.repository.uncross_out_the_queue_member(
            queue_member.user_id,
            queue_id
        )
        handler_context.repository.refresh_queues_last_time_updated_on(
            queue_id
        )
        handler_context.repository.commit()

        name = queue_member.user_info.get_formatted_name()
        handler_context.telegram_message_manager.send_message(
            update_context.chat_id,
            f"Участник {name} снова в очереди: {queue_name}"
        )
    finally:
        handler_context.telegram_message_manager.answer_callback_query(
            update_context.callback_query_id
        )


@callback_handler(constants.ButtonCallbackType.REMOVE_ME)
def handle_remove_me_callback(handler_context, update_context):
    try:
        user_info = update_context.sender_user_info
        queue_id = update_context.callback_query_data["queue_id"]
        queue_name = handler_context.repository.get_queue_name_by_queue_id(
            queue_id
        )
        success = handler_context.repository.remove_user_from_queue(
            user_info.id,
            queue_id
        )
        name = user_info.get_formatted_name()
        if not success:
            handler_context.telegram_message_manager.send_message(
                update_context.chat_id,
                f"{name} не состоит в данной очереди: {queue_name}"
            )
            return
        handler_context.repository.refresh_queues_last_time_updated_on(
            queue_id
        )
        handler_context.telegram_message_manager.send_message(
            update_context.chat_id,
            f"Участник {name} удален из очереди: {queue_name}"
        )
    finally:
        handler_context.repository.commit()
        handler_context.telegram_message_manager.answer_callback_query(
            update_context.callback_query_id
        )


@callback_handler(constants.ButtonCallbackType.NOOP)
def handle_noop_callback(handler_context, update_context):
    handler_context.telegram_message_manager.answer_callback_query(
        update_context.callback_query_id
    )


@callback_handler(constants.ButtonCallbackType.SHOW_NEXT_QUEUE_PAGE)
def handle_show_next_queue_page_callback(handler_context, update_context):
    try:
        main_button_type \
            = update_context.callback_query_data["main_button_type"]
        page_index = update_context.callback_query_data["page_index"]
        queue_pagination_reply_markup \
            = build_queue_pagination_reply_markup(
                handler_context.repository,
                page_index=page_index+1,
                page_size=constants.DEFAULT_QUEUES_PAGE_SIZE,
                main_button_type=main_button_type
            )
        if queue_pagination_reply_markup is None:
            handler_context.telegram_message_manager.send_message(
                update_context.chat_id,
                "Пока что нету ни одной доступной очереди."
            )
            return

        handler_context.telegram_message_manager.edit_message_reply_markup(
            update_context.chat_id,
            update_context.message_id,
            queue_pagination_reply_markup
        )
    finally:
        handler_context.telegram_message_manager.answer_callback_query(
            update_context.callback_query_id
        )


@callback_handler(constants.ButtonCallbackType.SHOW_PREVIOUS_QUEUE_PAGE)
def handle_show_previous_queue_page_callback(handler_context, update_context):
    try:
        main_button_type \
            = update_context.callback_query_data["main_button_type"]
        page_index = update_context.callback_query_data["page_index"]
        queue_pagination_reply_markup \
            = build_queue_pagination_reply_markup(
                handler_context.repository,
                page_index=page_index-1,
                page_size=constants.DEFAULT_QUEUES_PAGE_SIZE,
                main_button_type=main_button_type
            )
        if queue_pagination_reply_markup is None:
            handler_context.telegram_message_manager.send_message(
                update_context.chat_id,
                "Пока что нету ни одной доступной очереди."
            )
            return

        handler_context.telegram_message_manager.edit_message_reply_markup(
            update_context.chat_id,
            update_context.message_id,
            queue_pagination_reply_markup
        )
    finally:
        handler_context.telegram_message_manager.answer_callback_query(
            update_context.callback_query_id
        )


@callback_handler(constants.ButtonCallbackType.SHOW_QUEUE)
def handle_show_queue_callback(handler_context, update_context):
    try:
        queue_id = update_context.callback_query_data["queue_id"]
        queue_name = handler_context.repository.get_queue_name_by_queue_id(
            queue_id
        )
        if queue_name is None:
            handler_context.logger.log(
                LoggingLevel.WARN,
                "Received a /showqueue request for a non-existent queue "
                + f"with ID {queue_id}"
            )
            handler_context.telegram_message_manager.send_message(
                update_context.chat_id,
                f"Очереди с ID: {queue_id} не существует"
            )
            return
        queue_members = handler_context.repository \
            .get_queue_members_by_queue_id(queue_id)

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
        truncated_queue_description = truncate(
            queue_description,
            MAX_MESSAGE_LENGTH,
            constants.DEFAULT_TRUNCATED_MESSAGE_PLACEHOLDER
        )
        truncated_entities = truncate_entities(
            entities,
            MAX_MESSAGE_LENGTH
        )
        if truncated_queue_description != queue_description:
            handler_context.logger.log(
                LoggingLevel.WARN,
                "Forced to truncate message to fit the message limit of "
                + f"{MAX_MESSAGE_LENGTH} UTF-8 characters. Original "
                + f"message: {queue_description}\nOriginal entities: "
                + f"{entities}"
            )

        handler_context.telegram_message_manager.send_message(
            update_context.chat_id,
            truncated_queue_description,
            entities=truncated_entities
        )
    finally:
        handler_context.telegram_message_manager.answer_callback_query(
            update_context.callback_query_id
        )


@default_callback_handler
def handle_unknown_callback(handler_context, update_context):
    callback_type = update_context.callback_query_type
    handler_context.logger.log(
        LoggingLevel.ERROR,
        f"Received an unknown callback query type: {callback_type}"
    )
    handler_context.telegram_message_manager.send_message(
        update_context.chat_id,
        "???"
    )
    handler_context.telegram_message_manager.answer_callback_query(
        update_context.callback_query_id
    )


@default_command_handler
@default_response_handler
def handle_unknown_response(handler_context, update_context):
    handler_context.logger.log(
        LoggingLevel.WARN,
        f"Received an invalid command/response: {update_context.update}"
    )
    handler_context.telegram_message_manager.send_message(
        update_context.chat_id,
        "???"
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


def handle_generic_queue_command(
    handler_context,
    update_context,
    main_button_type,
    success_message
):
    queue_pagination_reply_markup = build_queue_pagination_reply_markup(
        handler_context.repository,
        page_index=1,
        page_size=constants.DEFAULT_QUEUES_PAGE_SIZE,
        main_button_type=main_button_type
    )
    if queue_pagination_reply_markup is None:
        handler_context.telegram_message_manager.send_message(
            update_context.chat_id,
            "Пока что нету ни одной доступной очереди."
        )
        return

    handler_context.telegram_message_manager.send_message(
        update_context.chat_id,
        success_message,
        queue_pagination_reply_markup
    )


def build_queue_pagination_reply_markup(
    repository,
    page_index,
    page_size,
    main_button_type
):
    total_queue_count = repository.get_total_queue_count()
    if total_queue_count == 0:
        return None

    queues_page = repository.get_queues_page(
        page_index,
        page_size
    )

    queue_choice_buttons = make_queue_choice_buttons(
        queues_page,
        page_index,
        page_size,
        total_queue_count,
        main_button_type
    )

    return {"inline_keyboard": queue_choice_buttons}


def make_queue_choice_buttons(
    queues_page,
    page_index,
    page_size,
    total_queue_count,
    main_button_type
):
    total_page_count = math.ceil(total_queue_count / page_size)
    is_first_page = page_index == 1
    is_last_page = page_index == total_page_count
    return list(map(
        lambda queue:
            [
                {
                    "text": queue.name,
                    "callback_data": json.dumps({
                        "type": main_button_type,
                        "queue_id": queue.id,
                    }),
                }
            ],
        queues_page
    )) + [[
        {
            "text": "<" if not is_first_page else "x",
            "callback_data":
                json.dumps({
                    "type": constants.ButtonCallbackType.NOOP,
                    "distinction_factor": random.random(),
                })
                if is_first_page
                else json.dumps({
                    "type":
                        constants.ButtonCallbackType.SHOW_PREVIOUS_QUEUE_PAGE,
                    "page_index": page_index,
                    "main_button_type": main_button_type,
                }),
        },
        {
            "text": f"{page_index}/{total_page_count}",
            "callback_data": json.dumps({
                "type": constants.ButtonCallbackType.NOOP,
                "distinction_factor": random.random(),
            }),
        },
        {
            "text": ">" if not is_last_page else "x",
            "callback_data":
                json.dumps({
                    "type": constants.ButtonCallbackType.NOOP,
                    "distinction_factor": random.random(),
                })
                if is_last_page
                else json.dumps({
                    "type": constants.ButtonCallbackType.SHOW_NEXT_QUEUE_PAGE,
                    "page_index": page_index,
                    "main_button_type": main_button_type,
                }),
        },
    ]]


def truncate(source, length, placeholder="..."):
    if len(source) > length:
        return source[:length - len(placeholder)] + placeholder
    return source


def truncate_entities(entities, length):
    return list(filter(
        lambda entity: entity["offset"] + entity["length"] <= length,
        entities
    ))
