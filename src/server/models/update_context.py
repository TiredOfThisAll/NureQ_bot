import json

from server.models.user_info import UserInfo


class UpdateContext:
    class Type:
        TEXT_MESSAGE = 1
        RESPONSE = 2
        CALLBACK_QUERY = 3
        OTHER = 4

    def from_update(update):
        update_context = UpdateContext()
        update_context.update = update

        # if has text and is NOT a reply
        if update.get("message", {}).get("text") is not None \
                and update.get("message", {}).get("reply_to_message") is None:
            update_context.type = UpdateContext.Type.TEXT_MESSAGE
            update_context.message = update_context.update["message"]
            update_context.sender_user_info = UserInfo.from_telegram_user_dict(
                update_context.message["from"]
            )
            update_context.message_text = update_context.message.get("text")
            update_context.chat_id = update_context.message["chat"]["id"]
            update_context.message_id = update["message"]["message_id"]
        # if is a reply
        elif update.get("message", {}).get("reply_to_message") is not None:
            update_context.type = UpdateContext.Type.RESPONSE
            update_context.message = update["message"]
            update_context.chat_id = update["message"]["chat"]["id"]
            update_context.responding_to_username = update.get("message") \
                .get("reply_to_message") \
                .get("from") \
                .get("username")
            update_context.response_text = update.get("message") \
                .get("reply_to_message") \
                .get("text")
            update_context.message_id = update["message"]["message_id"]
            if update["message"].get("text") is not None:
                update_context.response_type = UpdateContext.Type.TEXT_MESSAGE
                update_context.message_text = update["message"]["text"]
            else:
                update_context.response_type = UpdateContext.Type.OTHER
        # if is a callback query
        elif "callback_query" in update_context.update:
            update_context.type = UpdateContext.Type.CALLBACK_QUERY
            update_context.callback_query = update["callback_query"]
            update_context.callback_query_data = json.loads(
                update["callback_query"]["data"]
            )
            update_context.callback_query_type \
                = update_context.callback_query_data["type"]
            update_context.sender_user_info = UserInfo.from_telegram_user_dict(
                update_context.callback_query["from"]
            )
            update_context.chat_id \
                = update["callback_query"]["message"]["chat"]["id"]
            update_context.callback_query_id = update["callback_query"]["id"]
            update_context.message_id \
                = update["callback_query"]["message"]["message_id"]
        # if is something else
        else:
            update_context.type = UpdateContext.Type.OTHER
            update_context.update = update

        return update_context
