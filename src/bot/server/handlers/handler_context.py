class HandlerConfiguration:
    def __init__(self, queue_name_limit):
        self.queue_name_limit = queue_name_limit


class HandlerContext:
    def __init__(
        self,
        telegram_message_manager,
        repository,
        logger,
        configuration
    ):
        self.telegram_message_manager = telegram_message_manager
        self.repository = repository
        self.logger = logger
        self.configuration = configuration
