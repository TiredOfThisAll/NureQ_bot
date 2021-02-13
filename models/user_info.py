class UserInfo:
    def __init__(self, id, first_name, last_name, username):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.username = username

    def get_formatted_name(self):
        formatted_name = self.first_name
        if self.last_name is not None:
            formatted_name += " " + self.last_name
        return f"<a href='tg://user?id={self.id}'>{formatted_name}</a>"

    def from_telegram_user_dict(user_dict):
        return UserInfo(
            user_dict["id"],
            user_dict["first_name"],
            user_dict.get("last_name"),
            user_dict.get("username")
        )
