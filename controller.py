import math
import json
import random

from router import command_handler, response_handler, callback_handler, \
    default_callback_handler, default_command_handler, default_response_handler

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
    def __init__(self, telegram_message_manager, repository):
        self.telegram_message_manager = telegram_message_manager
        self.repository = repository

    @command_handler("/newqueue")
    def handle_new_queue_command(self, message):
        self.telegram_message_manager.send_message(
            message["chat"]["id"],
            NEW_QUEUE_COMMAND_RESPONSE_TEXT,
            reply_markup={"force_reply": True}
        )

    @command_handler("/showqueue")
    def handle_show_queue_command(self, message):
        self.handle_generic_queue_command(
            message,
            ButtonCallbackType.SHOW_QUEUE,
            "Выберите очередь, которую хотите посмотреть."
        )

    @command_handler("/crossout")
    def handle_cross_out_command(self, message):
        self.handle_generic_queue_command(
            message,
            ButtonCallbackType.CROSS_OUT,
            "Выберите очередь, из которой необходимо вычеркнуть участника"
        )

    @command_handler("/uncrossout")
    def handle_uncross_out_command(self, message):
        self.handle_generic_queue_command(
            message,
            ButtonCallbackType.UNCROSS_OUT,
            "Выберите очередь, в которую необходимо вернуть участника"
        )

    @command_handler("/addme")
    def handle_add_me_command(self, message):
        self.handle_generic_queue_command(
            message,
            ButtonCallbackType.ADD_ME,
            "Выберите очередь, в которую хотите добавиться."
        )

    @command_handler("/removeme")
    def handle_remove_me_command(self, message):
        self.handle_generic_queue_command(
            message,
            ButtonCallbackType.REMOVE_ME,
            "Выберите очередь, которую хотите покинуть."
        )

    @response_handler(NEW_QUEUE_COMMAND_RESPONSE_TEXT)
    def handle_new_queue_response(self, message):
        queue_name = message["text"]
        error = self.repository.create_queue(queue_name)
        if error == "INTEGRITY_ERROR":
            self.telegram_message_manager.send_message(
                message["chat"]["id"],
                "Очередь с именем " + queue_name + " уже существует"
            )
            return
        self.repository.commit()

        self.telegram_message_manager.send_message(
            message["chat"]["id"],
            "Создана новая очередь: " + queue_name
        )

    @callback_handler(ButtonCallbackType.ADD_ME)
    def handle_add_me_callback(
        self,
        callback_query,
        callback_query_data
    ):
        try:
            username = callback_query["from"]["username"]
            queue_id = callback_query_data["queue_id"]
            error = self.repository.add_me_to_queue(username, queue_id)
            self.repository.commit()
            queue_name = self.repository.get_queue_name_by_queue_id(queue_id)

            if error == "DUPLICATE_MEMBERS":
                self.telegram_message_manager.send_message(
                    callback_query["message"]["chat"]["id"],
                    "Вы уже состоите в данной очереди: " + queue_name
                )
                return
            if error == "NO_QUEUE":
                self.telegram_message_manager.send_message(
                    callback_query["message"]["chat"]["id"],
                    "Данной очереди не существует: " + queue_name
                )
                return
            self.telegram_message_manager.send_message(
                callback_query["message"]["chat"]["id"],
                "Вы добавлены в очередь: " + queue_name
            )
        finally:
            self.telegram_message_manager.answer_callback_query(
                callback_query["id"]
            )

    @callback_handler(ButtonCallbackType.CROSS_OUT)
    def handle_cross_out_callback(
        self,
        callback_query,
        callback_query_data
    ):
        try:
            queue_id = callback_query_data["queue_id"]
            username = self.repository.find_uncrossed_queue_member(queue_id)
            queue_name = self.repository.get_queue_name_by_queue_id(queue_id)

            if username is None:
                self.telegram_message_manager.send_message(
                    callback_query["message"]["chat"]["id"],
                    "В данной очереди не осталось участников: " + queue_name
                )
                return

            self.repository.cross_out_the_queue_member(username, queue_id)
            self.repository.commit()
            self.telegram_message_manager.send_message(
                callback_query["message"]["chat"]["id"],
                "Участник " + username + " вычеркнут из очереди: " + queue_name
            )
        finally:
            self.telegram_message_manager.answer_callback_query(
                callback_query["id"]
            )

    @callback_handler(ButtonCallbackType.UNCROSS_OUT)
    def handle_uncross_out_callback(
        self,
        callback_query,
        callback_query_data
    ):
        try:
            queue_id = callback_query_data["queue_id"]
            username = self.repository.find_last_crossed_queue_member(queue_id)
            queue_name = self.repository.get_queue_name_by_queue_id(queue_id)

            if username is None:
                self.telegram_message_manager.send_message(
                    callback_query["message"]["chat"]["id"],
                    "В данной очереди не осталось подходящих участников: "
                    + queue_name
                )
                return

            self.repository.uncross_out_the_queue_member(username, queue_id)
            self.repository.commit()
            self.telegram_message_manager.send_message(
                callback_query["message"]["chat"]["id"],
                "Участник " + username + " снова в очереди: " + queue_name
            )
        finally:
            self.telegram_message_manager.answer_callback_query(
                callback_query["id"]
            )

    @callback_handler(ButtonCallbackType.REMOVE_ME)
    def handle_remove_me_callback(
        self,
        callback_query,
        callback_query_data
    ):
        try:
            username = callback_query["from"]["username"]
            queue_id = callback_query_data["queue_id"]
            queue_name = self.repository.get_queue_name_by_queue_id(queue_id)
            success \
                = self.repository.remove_user_from_queue(username, queue_id)
            if not success:
                self.telegram_message_manager.send_message(
                    callback_query["message"]["chat"]["id"],
                    "Вы не состоите в данной очереди: " + queue_name
                )
                return
            self.repository.commit()
            self.telegram_message_manager.send_message(
                callback_query["message"]["chat"]["id"],
                "Участник " + username + " удален из очереди: " + queue_name
            )
        finally:
            self.telegram_message_manager.answer_callback_query(
                callback_query["id"]
            )

    @callback_handler(ButtonCallbackType.NOOP)
    def handle_noop_callback(self, callback_query):
        self.telegram_message_manager.answer_callback_query(
            callback_query["id"]
        )

    @callback_handler(ButtonCallbackType.SHOW_NEXT_QUEUE_PAGE)
    def handle_show_next_queue_page_callback(
        self,
        callback_query,
        callback_query_data
    ):
        try:
            main_button_type = callback_query_data["main_button_type"]
            queue_pagination_reply_markup \
                = build_queue_pagination_reply_markup(
                    self.repository,
                    page_index=callback_query_data["page_index"] + 1,
                    page_size=DEFAULT_QUEUES_PAGE_SIZE,
                    main_button_type=main_button_type
                )
            if queue_pagination_reply_markup is None:
                self.telegram_message_manager.send_message(
                    callback_query["message"]["chat"]["id"],
                    "Пока что нету ни одной доступной очереди."
                )
                return

            self.telegram_message_manager.edit_message_reply_markup(
                callback_query["message"]["chat"]["id"],
                callback_query["message"]["message_id"],
                queue_pagination_reply_markup
            )
        finally:
            self.telegram_message_manager.answer_callback_query(
                callback_query["id"]
            )

    @callback_handler(ButtonCallbackType.SHOW_PREVIOUS_QUEUE_PAGE)
    def handle_show_previous_queue_page_callback(
        self,
        callback_query,
        callback_query_data
    ):
        try:
            main_button_type = callback_query_data["main_button_type"]
            queue_pagination_reply_markup \
                = build_queue_pagination_reply_markup(
                    self.repository,
                    page_index=callback_query_data["page_index"] - 1,
                    page_size=DEFAULT_QUEUES_PAGE_SIZE,
                    main_button_type=main_button_type
                )
            if queue_pagination_reply_markup is None:
                self.telegram_message_manager.send_message(
                    callback_query["message"]["chat"]["id"],
                    "Пока что нету ни одной доступной очереди."
                )
                return

            self.telegram_message_manager.edit_message_reply_markup(
                callback_query["message"]["chat"]["id"],
                callback_query["message"]["message_id"],
                queue_pagination_reply_markup
            )
        finally:
            self.telegram_message_manager.answer_callback_query(
                callback_query["id"]
            )

    @callback_handler(ButtonCallbackType.SHOW_QUEUE)
    def handle_show_queue_callback(self, callback_query, callback_query_data):
        try:
            queue_id = callback_query_data["queue_id"]
            queue_name = self.repository.get_queue_name_by_queue_id(queue_id)
            if queue_name is None:
                self.telegram_message_manager.send_message(
                    callback_query["message"]["chat"]["id"],
                    "Очереди с ID: " + queue_id + " не существует"
                )
                return
            queue_members \
                = self.repository.get_queue_members_by_queue_id(queue_id)

            if len(queue_members) != 0:
                queue_description = f"{queue_name}:\n" + "".join(map(
                    lambda member_index: member_index[1].format_queue_string(
                        member_index[0] + 1
                    ),
                    enumerate(queue_members)
                ))
            else:
                queue_description = f"{queue_name}:\nОчередь пуста"

            self.telegram_message_manager.send_message(
                callback_query["message"]["chat"]["id"],
                queue_description,
                parse_mode="HTML"
            )
        finally:
            self.telegram_message_manager.answer_callback_query(
                callback_query["id"]
            )

    @default_callback_handler
    def handle_unknown_callback(self, callback_query, callback_query_data):
        callback_type = callback_query_data["type"]
        print(f"Received an unknown callback query type: {callback_type}")
        self.telegram_message_manager.send_message(
            callback_query["message"]["chat"]["id"],
            "???"
        )
        self.telegram_message_manager.answer_callback_query(
            callback_query["id"]
        )

    @default_command_handler
    @default_response_handler
    def handle_unknown_response(self, message):
        self.telegram_message_manager.send_message(
            message["chat"]["id"],
            "???"
        )

    def handle_error_while_processing_update(self, update):
        if "message" in update:
            chat_id = update["message"]["chat"]["id"]
        elif "callback_query" in update:
            chat_id = update["callback_query"]["message"]["chat"]["id"]
        else:
            return
        self.telegram_message_manager.send_message(chat_id, "Ошибка")

    def handle_generic_queue_command(
        self,
        message,
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
                message["chat"]["id"],
                "Пока что нету ни одной доступной очереди."
            )
            return

        self.telegram_message_manager.send_message(
            message["chat"]["id"],
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
