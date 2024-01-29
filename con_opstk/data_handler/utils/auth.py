
import jwt
import json
import time


def authenticate_headers(headers, secret_key, logger):

    headers = dict(headers)
    logger.info(f"Headers : {headers}")

    # Checking for presence of Authorization Header field
    if "Authorization" not in headers:
        return False
    
    # Checking for presence of 'Bearer' keyword
    bearer_token = headers["Authorization"]
    if bearer_token[0:7] != "Bearer ":
        logger.error("Bearer token not present")
        return False

    encoded_message = bearer_token[7:]

    #Decrypting message
    try:
        payload = jwt.decode(encoded_message, key=secret_key, algorithms="HS256")
    except Exception as e:
        logger.info("Message decoding failed")
        return False

    logger.info(f"Payload : {payload}")

    #Checking for token expiry
    if "exp" not in payload or payload["exp"] < time.time() :
        return False

    logger.info("Authentication Successful")
    return True



