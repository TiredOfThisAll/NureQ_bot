NEW_QUEUE_COMMAND_RESPONSE_TEXT \
    = "Введите имя новой очереди в ответ на это сообщение"
ADD_ME_TO_QUEUE_RESPONSE_TEXT \
    = "Введите имя очереди, к которой желаете присоедениться"


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

    def add_me_to_queue(self, message):
        self.telegram_message_manager.send_message(
            message["chat"]["id"],
            ADD_ME_TO_QUEUE_RESPONSE_TEXT
        )

    def respond_to_add_me_to_queue(self, message):
        queue_name = message["text"]
        username = message["from"]["username"]
        duplicate_members = self.repository \
            .add_me_to_queue(username, queue_name)
        if duplicate_members is None:
            self.telegram_message_manager.send_message(
                message["chat"]["id"],
                "Вы добавлены в очередь " + queue_name
            )
        elif duplicate_members == "Вы уже состоите в данной очереди ":
            self.telegram_message_manager.send_message(
                message["chat"]["id"],
                duplicate_members + queue_name
            )
        elif duplicate_members == "Данной очереди не существует ":
            self.telegram_message_manager.send_message(
                message["chat"]["id"],
                duplicate_members
            )

    def echo_message(self, message):
        self.telegram_message_manager.send_message(
            message["chat"]["id"],
            message["text"]
        )
