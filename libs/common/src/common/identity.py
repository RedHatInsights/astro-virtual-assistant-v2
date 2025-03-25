import abc

import quart
from werkzeug.exceptions import BadRequest

import injector
from common.session_storage import SessionStorage


class AbstractUserIdentityProvider(abc.ABC):
    async def get_user_identity(self) -> str: ...


class QuartWatsonExtensionUserIdentityProvider(AbstractUserIdentityProvider):
    def __init__(
        self, request: quart.Request, session_storage: injector.Inject[SessionStorage]
    ):
        self.request = request
        self.session_storage = session_storage

    async def get_user_identity(self):
        session_header_name = "x-rh-session-id"
        if session_header_name not in self.request.headers:
            raise BadRequest(f"Missing ${session_header_name}")

        session_id = self.request.headers[session_header_name]
        return (await self.session_storage.get(session_id)).user_identity


class QuartRedHatUserIdentityProvider(AbstractUserIdentityProvider):
    def __init__(self, request: quart.Request):
        self.request = request

    async def get_user_identity(self) -> str:
        session_header_name = "x-rh-identity"
        if session_header_name not in self.request.headers:
            raise BadRequest(f"Missing ${session_header_name}")

        return self.request.headers[session_header_name]


class FixedUserIdentityProvider(AbstractUserIdentityProvider):
    async def get_user_identity(self):
        """
        Fixed user identity equivalent to:
        {
           "identity":{
              "account_number":"account123",
              "org_id":"org123",
              "type":"User",
              "user":{
                 "is_org_admin":true,
                 "is_internal": true,
                 "user_id":"1234567890",
                 "username":"astro"
              },
              "internal":{
                 "org_id":"org123"
              }
           }
        }
        """

        return "eyJpZGVudGl0eSI6eyJhY2NvdW50X251bWJlciI6ImFjY291bnQxMjMiLCJvcmdfaWQiOiJvcmcxMjMiLCJ0eXBlIjoiVXNlciIsInVzZXIiOnsiaXNfb3JnX2FkbWluIjp0cnVlLCJpc19pbnRlcm5hbCI6dHJ1ZSwidXNlcl9pZCI6IjEyMzQ1Njc4OTAiLCJ1c2VybmFtZSI6ImFzdHJvIn0sImludGVybmFsIjp7Im9yZ19pZCI6Im9yZzEyMyJ9fX0="
