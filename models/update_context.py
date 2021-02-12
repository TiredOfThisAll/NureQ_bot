from user_info import UserInfo


class UpdateContext:
    class Type:
        MESSAGE = 1
        CALLBACK_QUERY = 2

    def from_update(update):
        update_context = UpateContext()
        update_context.update = update

        if "message" in update_context.update:
            update_context.type = Type.MESSAGE
            update_context.message = update_context.update["message"]
            update_context.sender_user_info = UserInfo.from_telegram_user_dict(
                update_context.message["from"]
            )
            update_context.message_text = update_context.message.get("text")
            update_context.is_reply \
                = "reply_to_message" in update_context.message
            update_context.response_text = update_context.message \
                .get("reply_to_message", {}) \
                .get("text")
        elif "callback_query" in update_context.update:
            update_context.type = Type.CALLBACK_QUERY
            update_context.callback_query_data = json.loads(
                update_context.update["callback_query"]["data"]
            )
            update_context.callback_query_type \
                = update_context.update["callback_query_data"]["type"]
            update_context.sender_user_info = UserInfo.from_telegram_user_dict(
                update_context.callback_query["from"]
            )
        else:
            update_context.type = None
