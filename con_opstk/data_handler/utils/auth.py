
import jwt
import json
import time


def authenticate_headers(headers, secret_key):

    if "Authorization" not in headers:
        return False
    
    encoded_message = headers["Authorization"]

    try:
        decoded_message = jwt.decode(encoded_message, key=secret_key, algorithms="HS256")
    except Exception as e:
        return False

    payload = json.loads(decoded_message)

    if "exp" not in payload or payload["exp"] < time.time() :
        return False


    return True




