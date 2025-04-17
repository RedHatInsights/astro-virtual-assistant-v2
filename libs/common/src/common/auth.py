from __future__ import annotations

import binascii

from quart import request, jsonify
import base64
import functools
import json


def check_identity(identity_header):
    try:
        base64.b64decode(identity_header)
    except binascii.Error:
        return False
    return True


def require_identity_header(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        identity_header = request.headers.get("x-rh-identity")
        if not identity_header or not check_identity(identity_header):
            return jsonify(message="Invalid x-rh-identity"), 401
        return await func(*args, **kwargs)

    return wrapper


def assistant_user_id(identity):
    decoded_identity = base64.b64decode(identity).decode("utf8")
    identity_wrapper = json.loads(decoded_identity)
    identity_json = identity_wrapper["identity"]

    org_id = identity_json["org_id"]
    identity_type = identity_json["type"]
    if identity_type == "ServiceAccount":
        user_id = identity_json["service_account"]["user_id"]
    elif identity_type == "User":
        user_id = identity_json["user"]["user_id"]
    elif identity_type == "System":
        auth_type = identity_json["auth_type"]
        if auth_type == "uhc-auth":
            user_id = "cluster-" + identity_json["system"]["cluster_id"]
        elif auth_type == "cert-auth":
            user_id = identity_json["system"]["cn"]
        else:
            raise ValueError(f"Invalid auth_type for System identity: {auth_type}")
    else:
        raise ValueError(f"Invalid identity_type identity: {identity_type}")

    return f"{org_id}/{user_id}"


def decoded_identity_header(identity):
    decoded_identity = base64.b64decode(identity).decode("utf8")
    return json.loads(decoded_identity)
