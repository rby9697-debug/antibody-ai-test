from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class Depends:
    dependency: Callable[..., Any]


class APIRouter:
    def __init__(self, prefix: str = "", tags: list[str] | None = None):
        self.prefix = prefix
        self.tags = tags or []
        self.routes: dict[tuple[str, str], Callable[..., Any]] = {}

    def get(self, path: str):
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.routes[("GET", f"{self.prefix}{path}")] = func
            return func

        return decorator


class FastAPI:
    def __init__(self):
        self.routes: dict[tuple[str, str], Callable[..., Any]] = {}
        self.dependency_overrides: dict[Callable[..., Any], Callable[..., Any]] = {}

    def include_router(self, router: APIRouter) -> None:
        self.routes.update(router.routes)
