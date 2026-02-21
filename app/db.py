from collections.abc import Generator

from sqlalchemy.orm import Session


def get_db() -> Generator[Session, None, None]:
    raise NotImplementedError("Bind this dependency to your existing session provider.")
    yield
