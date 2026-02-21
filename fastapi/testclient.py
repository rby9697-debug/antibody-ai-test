from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends


@dataclass
class Response:
    status_code: int
    _json: dict

    def json(self):
        return self._json


class TestClient:
    def __init__(self, app):
        self.app = app

    def get(self, path: str) -> Response:
        for (method, route_path), func in self.app.routes.items():
            if method != "GET":
                continue
            parts_r = route_path.strip("/").split("/")
            parts_p = path.strip("/").split("/")
            if len(parts_r) != len(parts_p):
                continue

            kwargs = {}
            matched = True
            for rp, pp in zip(parts_r, parts_p):
                if rp.startswith("{") and rp.endswith("}"):
                    kwargs[rp[1:-1]] = pp
                elif rp != pp:
                    matched = False
                    break
            if not matched:
                continue

            db_dep = func.__defaults__[0]
            if isinstance(db_dep, Depends):
                dep = db_dep.dependency
                dep = self.app.dependency_overrides.get(dep, dep)
                kwargs["db"] = dep()

            return Response(status_code=200, _json=func(**kwargs))

        return Response(status_code=404, _json={"detail": "Not Found"})
