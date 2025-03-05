from pydantic import BaseModel


class RHSessionIdHeader(BaseModel):
    x_rh_session_id: str
