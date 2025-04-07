import base64

from common.auth import assistant_user_id

from .. import get_resource_contents


def load_and_base64encode_resource(resource: str):
    data = get_resource_contents(resource)
    return base64.b64encode(data.encode())


async def test_identity_basic():
    token = load_and_base64encode_resource("identities/basic.json")
    assert assistant_user_id(token) == "321/1212"


async def test_identity_cert():
    token = load_and_base64encode_resource("identities/cert.json")
    assert assistant_user_id(token) == "321/c87dcb4c-8af1-40dd-878e-60c744edddd0"


async def test_identity_jwt():
    token = load_and_base64encode_resource("identities/jwt.json")
    assert assistant_user_id(token) == "321/1212"


async def test_identity_service_account():
    token = load_and_base64encode_resource("identities/service-account.json")
    assert assistant_user_id(token) == "321/60ce65dc-4b5a-4812-8b65-b48178d92b12"


async def test_identity_uhc():
    token = load_and_base64encode_resource("identities/uhc.json")
    assert assistant_user_id(token) == "321/cluster-456"
