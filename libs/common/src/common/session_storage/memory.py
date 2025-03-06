from typing import Optional

from . import Session, SessionStorage


class MemorySessionStorage(SessionStorage):
    """
    Memory session storage - only to be used for testing purposes
    """

    def __init__(self):
        super().__init__()
        self.storage = {}

    async def retrieve(self, session_key: str) -> Optional[Session]:
        return self.storage.get(session_key, None)

    async def store(self, session: Session):
        self.storage[session.key] = session
