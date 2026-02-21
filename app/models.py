from dataclasses import dataclass
from enum import Enum


class Role(str, Enum):
    admin = "admin"
    project_manager = "project_manager"
    scientist = "scientist"
    read_only = "read_only"


@dataclass(slots=True)
class User:
    username: str
    role: Role
