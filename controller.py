from telegram_message_manager import TelegramMessageManager

NEW_QUEUE_COMMAND_RESPONSE_TEXT \
    = "Введите имя новой очереди в ответ на это сообщение"


class Controller:
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id

    def prompt_queue_name(self):
        telegram_message_manager = TelegramMessageManager(self.token)
        telegram_message_manager.send_message(
            self.chat_id,
            NEW_QUEUE_COMMAND_RESPONSE_TEXT
        )

    def respond_to_prompted_queue_name(self, text):
        telegram_message_manager = TelegramMessageManager(self.token)
        telegram_message_manager.send_message(
            self.chat_id,
            "Создана новая очередь: " + text
        )

    def echo_message(self, text):
        telegram_message_manager = TelegramMessageManager(self.token)
        telegram_message_manager.send_message(self.chat_id, text)
