import abc

import quart
from werkzeug.exceptions import BadRequest

import injector
from common.session_storage import SessionStorage
from common.auth import decoded_identity_header


class AbstractUserIdentityProvider(abc.ABC):
    async def get_user_identity(self) -> str: ...

    async def is_internal(self) -> bool:
        identity = decoded_identity_header(
            await self.user_identity_provider.get_user_identity()
        )
        return identity['user']['is_internal']


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
                 "username":"astro",
                 "email":"email@email.com"
              },
              "internal":{
                 "org_id":"org123"
              }
           }
        }
        """

        return "eyJpZGVudGl0eSI6eyJhY2NvdW50X251bWJlciI6ImFjY291bnQxMjMiLCJvcmdfaWQiOiJvcmcxMjMiLCJ0eXBlIjoiVXNlciIsInVzZXIiOnsiaXNfb3JnX2FkbWluIjp0cnVlLCJpc19pbnRlcm5hbCI6dHJ1ZSwidXNlcl9pZCI6IjEyMzQ1Njc4OTAiLCJ1c2VybmFtZSI6ImFzdHJvIiwiZW1haWwiOiJlbWFpbEBlbWFpbC5jb20ifSwiaW50ZXJuYWwiOnsib3JnX2lkIjoib3JnMTIzIn19fQ=="

    async def is_internal(self) -> bool:
        return True
