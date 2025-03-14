import pickle
from os.path import exists
from typing import Optional

from . import Session, SessionStorage


class FileSessionStorage(SessionStorage):
    """
    File session storage - only to be used for testing purposes when running both services in the same machine
    Only as an example
    """

    def __init__(self, filename):
        super().__init__()
        self.filename = filename

    async def retrieve(self, session_key: str) -> Optional[Session]:
        if not exists(self.filename):
            return None

        storage = pickle.load(open(self.filename, "rb"))
        if storage is None:
            return None

        return storage.get(session_key, None)

    async def store(self, session: Session):
        if exists(self.filename):
            storage = pickle.load(open(self.filename, "r+b"))
        else:
            storage = {}

        storage[session.key] = session
        # noinspection PyTypeChecker
        pickle.dump(storage, open(self.filename, "w+b"))
