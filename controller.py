from telegram_message_manager import TelegramMessageManager

NEW_QUEUE_COMMAND_RESPONSE_TEXT \
    = "Введите имя новой очереди в ответ на это сообщение"


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
        self.repository.create_queue(queue_name)
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
