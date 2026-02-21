"""Minimal WSGI app exposing GET /search?q=... for archive global search."""

from __future__ import annotations

import json
from urllib.parse import parse_qs

from src.search_service import run_search


def application(environ, start_response):
    path = environ.get("PATH_INFO", "")
    method = environ.get("REQUEST_METHOD", "GET")

    if method == "GET" and path == "/search":
        qs = parse_qs(environ.get("QUERY_STRING", ""))
        q = (qs.get("q") or [""])[0]

        # deferred import so unit tests can inject fake cursor without psycopg
        import psycopg

        conninfo = environ.get("ARCHIVE_DATABASE_DSN", "")
        with psycopg.connect(conninfo) as conn:
            with conn.cursor() as cur:
                result = run_search(cur, q)

        body = json.dumps({"projects": result.projects, "hits": result.hits}).encode("utf-8")
        start_response("200 OK", [("Content-Type", "application/json"), ("Content-Length", str(len(body)))])
        return [body]

    body = b'{"error":"not found"}'
    start_response("404 Not Found", [("Content-Type", "application/json"), ("Content-Length", str(len(body)))])
    return [body]
