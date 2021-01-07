import math
import json
import random

NEW_QUEUE_COMMAND_RESPONSE_TEXT \
    = "Введите имя новой очереди в ответ на это сообщение"
DEFAULT_QUEUES_PAGE_SIZE = 3


class ButtonCallbackType:
    NOOP = "NOOP"
    SHOW_NEXT_QUEUE_PAGE = "SHOW_NEXT_QUEUE_PAGE"
    SHOW_PREVIOUS_QUEUE_PAGE = "SHOW_PREVIOUS_QUEUE_PAGE"
    SHOW_QUEUE = "SHOW_QUEUE"


class Controller:
    def __init__(self, telegram_message_manager, repository):
        self.telegram_message_manager = telegram_message_manager
        self.repository = repository

    def prompt_queue_name(self, message):
        self.telegram_message_manager.send_message(
            message["chat"]["id"],
            NEW_QUEUE_COMMAND_RESPONSE_TEXT
        )

    def respond_to_prompted_queue_name(self, message):
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

    def echo_message(self, message):
        self.telegram_message_manager.send_message(
            message["chat"]["id"],
            message["text"]
        )

    def prompt_queue_name_to_show(self, message):
        total_queue_count = self.repository.get_total_queue_count()
        if total_queue_count == 0:
            self.telegram_message_manager.send_message(
                message["chat"]["id"],
                "Пока что нету ни одной доступной очереди."
            )
            return

        page_index = 1
        page_size = DEFAULT_QUEUES_PAGE_SIZE
        first_queues_page = self.repository.get_queues_page(
            page_index=page_index,
            page_size=page_size
        )

        queue_choice_buttons = make_queue_choice_buttons(
            first_queues_page,
            page_index,
            page_size,
            total_queue_count
        )
        self.telegram_message_manager.send_message(
            message["chat"]["id"],
            "Выберите очередь, которую хотите посмотреть.",
            reply_markup={
                "inline_keyboard": queue_choice_buttons,
            }
        )

    def handle_noop_callback(self, callback_query):
        self.telegram_message_manager.answer_callback_query(
            callback_query["id"]
        )


def make_queue_choice_buttons(
    queues_page,
    page_index,
    page_size,
    total_queue_count
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
                        "type": ButtonCallbackType.SHOW_QUEUE,
                        "queue_id": queue.id,
                    }),
                }
            ],
        queues_page
    )) + [[
        {
            "text": "<" if not is_first_page else "x",
            "callback_data":
                json.dumps({"type": ButtonCallbackType.NOOP})
                if is_first_page
                else json.dumps({
                    "type": ButtonCallbackType.SHOW_PREVIOUS_QUEUE_PAGE,
                    "current_page_index": page_index,
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
                    "current_page_index": page_index,
                }),
        },
    ]]
