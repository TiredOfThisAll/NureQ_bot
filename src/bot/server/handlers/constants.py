NEW_QUEUE_COMMAND_RESPONSE_TEXT \
    = "Введите имя новой очереди в ответ на это сообщение"
QUEUE_NAME_ONLY_TEXT_RESPONSE_TEXT \
    = "Имя очереди должно быть введено в текстовом формате"
QUEUE_NAME_TOO_LONG_RESPONSE_TEXT \
    = "Имя очереди не должно быть длиннее {} символов"
DEFAULT_QUEUES_PAGE_SIZE = 3
DEFAULT_TRUNCATED_MESSAGE_PLACEHOLDER = "...\n[Обрезано]"


class ButtonCallbackType:
    NOOP = 1
    SHOW_NEXT_QUEUE_PAGE = 2
    SHOW_PREVIOUS_QUEUE_PAGE = 3
    SHOW_QUEUE = 4
    ADD_ME = 5
    CROSS_OUT = 6
    UNCROSS_OUT = 7
    REMOVE_ME = 8
