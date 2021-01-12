class QueueMember:
    def __init__(self, id, member_name, queue_id, crossed):
        self.id = id
        self.member_name = member_name
        self.queue_id = queue_id
        self.crossed = crossed

    def from_tuple(queue_member_tuple):
        return QueueMember(
            queue_member_tuple[0],
            queue_member_tuple[1],
            queue_member_tuple[2],
            queue_member_tuple[3]
        )

    def __str__(self):
        return "QueueMember: id = " + str(self.id) + ", member_name = " \
            + self.member_name + ", queue_id = " + str(self.queue_id)
