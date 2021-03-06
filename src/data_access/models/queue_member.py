from bot.server.models.user_info import UserInfo


class QueueMember:
    def __init__(
        self,
        id,
        user_id,
        user_first_name,
        user_last_name,
        user_username,
        queue_id,
        crossed
    ):
        self.id = id
        self.user_id = user_id
        self.user_first_name = user_first_name
        self.user_last_name = user_last_name
        self.user_username = user_username
        self.queue_id = queue_id
        self.crossed = crossed
        self.user_info = UserInfo(
            user_id,
            user_first_name,
            user_last_name,
            user_username
        )

    def from_tuple(queue_member_tuple):
        return QueueMember(
            queue_member_tuple[0],
            queue_member_tuple[1],
            queue_member_tuple[2],
            queue_member_tuple[3],
            queue_member_tuple[4],
            queue_member_tuple[5],
            queue_member_tuple[6],
        )

    def get_formatted_queue_string(self, queue_pos):
        formatted_queue_string \
            = f"{queue_pos}. {self.user_info.get_formatted_name()}"
        if self.crossed == 1:
            formatted_queue_string = f"<s>{formatted_queue_string}</s>"
        return formatted_queue_string

    def __str__(self):
        return "QueueMember: " \
            + f"id = {self.id}, " \
            + f"user_id = {self.user_id}, " \
            + f"user_first_name = {self.user_first_name}, " \
            + f"user_last_name = {self.user_last_name}, " \
            + f"user_username = {self.user_username}, " \
            + f"queue_id = {self.queue_id}, " \
            + f"crossed = {self.crossed}"
