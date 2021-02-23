import math
import json
import random

from server.router import command_handler, response_handler, \
    callback_handler, default_callback_handler, default_command_handler, \
    default_response_handler
from services.logging import LoggingLevel

NEW_QUEUE_COMMAND_RESPONSE_TEXT \
    = "Введите имя новой очереди в ответ на это сообщение"
DEFAULT_QUEUES_PAGE_SIZE = 3


class ButtonCallbackType:
    NOOP = 1
    SHOW_NEXT_QUEUE_PAGE = 2
    SHOW_PREVIOUS_QUEUE_PAGE = 3
    SHOW_QUEUE = 4
    ADD_ME = 5
    CROSS_OUT = 6
    UNCROSS_OUT = 7
    REMOVE_ME = 8


class Controller:
    def __init__(self, telegram_message_manager, repository, logger):
        self.telegram_message_manager = telegram_message_manager
        self.repository = repository
        self.logger = logger

    @command_handler("/start")
    @command_handler("/start@NureQ_bot")
    def handle_start_command(self, update_context):
        self.telegram_message_manager.send_message(
            update_context.chat_id,
            "Йоу"
        )

    @command_handler("/newqueue")
    @command_handler("/newqueue@NureQ_bot")
    def handle_new_queue_command(self, update_context):
        self.telegram_message_manager.send_message(
            update_context.chat_id,
            NEW_QUEUE_COMMAND_RESPONSE_TEXT,
            reply_markup={"force_reply": True}
        )

    @command_handler("/showqueue")
    @command_handler("/showqueue@NureQ_bot")
    def handle_show_queue_command(self, update_context):
        self.handle_generic_queue_command(
            update_context,
            ButtonCallbackType.SHOW_QUEUE,
            "Выберите очередь, которую хотите посмотреть."
        )

    @command_handler("/crossout")
    @command_handler("/crossout@NureQ_bot")
    def handle_cross_out_command(self, update_context):
        self.handle_generic_queue_command(
            update_context,
            ButtonCallbackType.CROSS_OUT,
            "Выберите очередь, из которой необходимо вычеркнуть участника"
        )

    @command_handler("/uncrossout")
    @command_handler("/uncrossout@NureQ_bot")
    def handle_uncross_out_command(self, update_context):
        self.handle_generic_queue_command(
            update_context,
            ButtonCallbackType.UNCROSS_OUT,
            "Выберите очередь, в которую необходимо вернуть участника"
        )

    @command_handler("/addme")
    @command_handler("/addme@NureQ_bot")
    def handle_add_me_command(self, update_context):
        self.handle_generic_queue_command(
            update_context,
            ButtonCallbackType.ADD_ME,
            "Выберите очередь, в которую хотите добавиться."
        )

    @command_handler("/removeme")
    @command_handler("/removeme@NureQ_bot")
    def handle_remove_me_command(self, update_context):
        self.handle_generic_queue_command(
            update_context,
            ButtonCallbackType.REMOVE_ME,
            "Выберите очередь, которую хотите покинуть."
        )

    @response_handler(NEW_QUEUE_COMMAND_RESPONSE_TEXT)
    def handle_new_queue_response(self, update_context):
        queue_name = update_context.message_text
        error = self.repository.create_queue(queue_name)
        if error == "QUEUE_NAME_DUPLICATE":
            self.telegram_message_manager.send_message(
                update_context.chat_id,
                f"Очередь с именем {queue_name} уже существует"
            )
            return
        if error == "NOT_NULL_CONSTRAINT_FAILED":
            self.telegram_message_manager.send_message(
                update_context.chat_id,
                f"Имя очереди должно быть введено в текстовом формате"
            )
            return
        self.repository.commit()

        self.telegram_message_manager.send_message(
            update_context.chat_id,
            f"Создана новая очередь: {queue_name}"
        )

    @callback_handler(ButtonCallbackType.ADD_ME)
    def handle_add_me_callback(self, update_context):
        try:
            queue_id = update_context.callback_query_data["queue_id"]
            error = self.repository.add_me_to_queue(
                update_context.sender_user_info.id,
                update_context.sender_user_info.first_name,
                update_context.sender_user_info.last_name,
                update_context.sender_user_info.username,
                queue_id
            )
            queue_name = self.repository.get_queue_name_by_queue_id(queue_id)
            name = update_context.sender_user_info.get_formatted_name()
            if error == "DUPLICATE_MEMBERS":
                self.telegram_message_manager.send_message(
                    update_context.chat_id,
                    f"{name} уже состоит в данной очереди: {queue_name}"
                )
                return
            if error == "NO_QUEUE":
                self.logger.log(
                    LoggingLevel.WARN,
                    f"Received an /addme request for a non-existent queue "
                    + "with ID {queue_id}"
                )
                self.telegram_message_manager.send_message(
                    update_context.chat_id,
                    "Данной очереди не существует: " + queue_name
                )
                return
            self.repository.refresh_queues_last_time_updated_on(queue_id)
            self.repository.commit()
            self.telegram_message_manager.send_message(
                update_context.chat_id,
                f"{name} добавлен(а) в очередь: {queue_name}"
            )
        finally:
            self.telegram_message_manager.answer_callback_query(
                update_context.callback_query_id
            )

    @callback_handler(ButtonCallbackType.CROSS_OUT)
    def handle_cross_out_callback(self, update_context):
        try:
            queue_id = update_context.callback_query_data["queue_id"]
            queue_member \
                = self.repository.find_uncrossed_queue_member(queue_id)
            queue_name = self.repository.get_queue_name_by_queue_id(queue_id)

            if queue_member is None:
                self.telegram_message_manager.send_message(
                    update_context.chat_id,
                    f"В данной очереди не осталось участников: {queue_name}"
                )
                return

            self.repository.cross_out_queue_member(
                queue_member.user_id,
                queue_id
            )
            self.repository.refresh_queues_last_time_updated_on(queue_id)
            self.repository.commit()

            name = queue_member.user_info.get_formatted_name()
            self.telegram_message_manager.send_message(
                update_context.chat_id,
                f"Участник {name} вычеркнут из очереди: {queue_name}"
            )
        finally:
            self.telegram_message_manager.answer_callback_query(
                update_context.callback_query_id
            )

    @callback_handler(ButtonCallbackType.UNCROSS_OUT)
    def handle_uncross_out_callback(self, update_context):
        try:
            queue_id = update_context.callback_query_data["queue_id"]
            queue_member = self.repository.find_last_crossed_queue_member(
                queue_id
            )
            queue_name = self.repository.get_queue_name_by_queue_id(queue_id)

            if queue_member is None:
                self.telegram_message_manager.send_message(
                    update_context.chat_id,
                    "В данной очереди не осталось подходящих участников: "
                    + queue_name
                )
                return

            self.repository.uncross_out_the_queue_member(
                queue_member.user_id,
                queue_id
            )
            self.repository.refresh_queues_last_time_updated_on(queue_id)
            self.repository.commit()

            name = queue_member.user_info.get_formatted_name()
            self.telegram_message_manager.send_message(
                update_context.chat_id,
                f"Участник {name} снова в очереди: {queue_name}"
            )
        finally:
            self.telegram_message_manager.answer_callback_query(
                update_context.callback_query_id
            )

    @callback_handler(ButtonCallbackType.REMOVE_ME)
    def handle_remove_me_callback(self, update_context):
        try:
            user_info = update_context.sender_user_info
            queue_id = update_context.callback_query_data["queue_id"]
            queue_name = self.repository.get_queue_name_by_queue_id(queue_id)
            success = self.repository.remove_user_from_queue(
                user_info.id,
                queue_id
            )
            name = user_info.get_formatted_name()
            if not success:
                self.telegram_message_manager.send_message(
                    update_context.chat_id,
                    f"{name} не состоит в данной очереди: {queue_name}"
                )
                return
            self.repository.refresh_queues_last_time_updated_on(queue_id)
            self.repository.commit()
            self.telegram_message_manager.send_message(
                update_context.chat_id,
                f"Участник {name} удален из очереди: {queue_name}"
            )
        finally:
            self.telegram_message_manager.answer_callback_query(
                update_context.callback_query_id
            )

    @callback_handler(ButtonCallbackType.NOOP)
    def handle_noop_callback(self, update_context):
        self.telegram_message_manager.answer_callback_query(
            update_context.callback_query_id
        )

    @callback_handler(ButtonCallbackType.SHOW_NEXT_QUEUE_PAGE)
    def handle_show_next_queue_page_callback(self, update_context):
        try:
            main_button_type \
                = update_context.callback_query_data["main_button_type"]
            page_index = update_context.callback_query_data["page_index"]
            queue_pagination_reply_markup \
                = build_queue_pagination_reply_markup(
                    self.repository,
                    page_index=page_index+1,
                    page_size=DEFAULT_QUEUES_PAGE_SIZE,
                    main_button_type=main_button_type
                )
            if queue_pagination_reply_markup is None:
                self.telegram_message_manager.send_message(
                    update_context.chat_id,
                    "Пока что нету ни одной доступной очереди."
                )
                return

            self.telegram_message_manager.edit_message_reply_markup(
                update_context.chat_id,
                update_context.message_id,
                queue_pagination_reply_markup
            )
        finally:
            self.telegram_message_manager.answer_callback_query(
                update_context.callback_query_id
            )

    @callback_handler(ButtonCallbackType.SHOW_PREVIOUS_QUEUE_PAGE)
    def handle_show_previous_queue_page_callback(self, update_context):
        try:
            main_button_type \
                = update_context.callback_query_data["main_button_type"]
            page_index = update_context.callback_query_data["page_index"]
            queue_pagination_reply_markup \
                = build_queue_pagination_reply_markup(
                    self.repository,
                    page_index=page_index-1,
                    page_size=DEFAULT_QUEUES_PAGE_SIZE,
                    main_button_type=main_button_type
                )
            if queue_pagination_reply_markup is None:
                self.telegram_message_manager.send_message(
                    update_context.chat_id,
                    "Пока что нету ни одной доступной очереди."
                )
                return

            self.telegram_message_manager.edit_message_reply_markup(
                update_context.chat_id,
                update_context.message_id,
                queue_pagination_reply_markup
            )
        finally:
            self.telegram_message_manager.answer_callback_query(
                update_context.callback_query_id
            )

    @callback_handler(ButtonCallbackType.SHOW_QUEUE)
    def handle_show_queue_callback(self, update_context):
        try:
            queue_id = update_context.callback_query_data["queue_id"]
            queue_name = self.repository.get_queue_name_by_queue_id(queue_id)
            if queue_name is None:
                self.logger.log(
                    LoggingLevel.WARN,
                    f"Received a /showqueue request for a non-existent queue "
                    + "with ID {queue_id}"
                )
                self.telegram_message_manager.send_message(
                    update_context.chat_id,
                    f"Очереди с ID: {queue_id} не существует"
                )
                return
            queue_members \
                = self.repository.get_queue_members_by_queue_id(queue_id)

            if len(queue_members) != 0:
                queue_description = f"{queue_name}:\n" + "\n".join(map(
                    lambda member_index: member_index[1]
                    .get_formatted_queue_string(member_index[0] + 1),
                    enumerate(queue_members)
                ))
            else:
                queue_description = f"{queue_name}:\nОчередь пуста"

            self.telegram_message_manager.send_message(
                update_context.chat_id,
                queue_description
            )
        finally:
            self.telegram_message_manager.answer_callback_query(
                update_context.callback_query_id
            )

    @default_callback_handler
    def handle_unknown_callback(self, update_context):
        callback_type = update_context.callback_query_type
        self.logger.log(
            LoggingLevel.ERROR,
            f"Received an unknown callback query type: {callback_type}"
        )
        self.telegram_message_manager.send_message(
            update_context.chat_id,
            "???"
        )
        self.telegram_message_manager.answer_callback_query(
            update_context.callback_query_id
        )

    @default_command_handler
    @default_response_handler
    def handle_unknown_response(self, update_context):
        self.logger.log(
            LoggingLevel.WARN,
            f"Received an invalid command/response: {update_context.update}"
        )
        self.telegram_message_manager.send_message(
            update_context.chat_id,
            "???"
        )

    def handle_error_while_processing_update(self, update_context):
        try:
            self.telegram_message_manager.send_message(
                update_context.chat_id,
                "Ошибка"
            )
        except Exception:
            pass

    def handle_generic_queue_command(
        self,
        update_context,
        main_button_type,
        success_message
    ):
        queue_pagination_reply_markup = build_queue_pagination_reply_markup(
            self.repository,
            page_index=1,
            page_size=DEFAULT_QUEUES_PAGE_SIZE,
            main_button_type=main_button_type
        )
        if queue_pagination_reply_markup is None:
            self.telegram_message_manager.send_message(
                update_context.chat_id,
                "Пока что нету ни одной доступной очереди."
            )
            return

        self.telegram_message_manager.send_message(
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
                    "type": ButtonCallbackType.NOOP,
                    "distinction_factor": random.random(),
                })
                if is_first_page
                else json.dumps({
                    "type": ButtonCallbackType.SHOW_PREVIOUS_QUEUE_PAGE,
                    "page_index": page_index,
                    "main_button_type": main_button_type,
                }),
        },
        {
            "text": f"{page_index}/{total_page_count}",
            "callback_data": json.dumps({
                "type": ButtonCallbackType.NOOP,
                "distinction_factor": random.random(),
            }),
        },
        {
            "text": ">" if not is_last_page else "x",
            "callback_data":
                json.dumps({
                    "type": ButtonCallbackType.NOOP,
                    "distinction_factor": random.random(),
                })
                if is_last_page
                else json.dumps({
                    "type": ButtonCallbackType.SHOW_NEXT_QUEUE_PAGE,
                    "page_index": page_index,
                    "main_button_type": main_button_type,
                }),
        },
    ]]
