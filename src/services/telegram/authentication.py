from hashlib import sha256
import hmac


def validate_login(auth_data, bot_token):
    auth_data_list = []
    for key, value in auth_data.items():
        if key != "hash":
            auth_data_list.append(f"{key}={value}")
    data_check_string = "\n".join(sorted(auth_data_list))
    secret_key = sha256(bot_token).digest()
    expected_hash = hmac.new(secret_key, data_check_string.encode(), sha256)\
        .hexdigest()
    return expected_hash == auth_data["hash"]
