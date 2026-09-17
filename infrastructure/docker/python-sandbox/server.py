"""Runs as the sandbox container's entrypoint (PID 1). Wraps a single
persistent `PythonKernel` behind a Unix domain socket — a filesystem-based
IPC channel, not a network one, so it keeps working even with the container
started `network_mode="none"` (see docs/architecture.md#python-lab-phase-4).

The host side never connects to this socket directly; it runs `client.py`
via `docker exec` (see `app/python_lab/docker_backend.py`), which connects
to this socket from *inside* the container's own namespace and relays one
request/response pair, then exits. One request per connection — no need for
a persistent connection since `docker exec` spins up a fresh client process
per call anyway, and this keeps the protocol trivial to reason about.
"""

from __future__ import annotations

import dataclasses
import json
import os
import socket
import socketserver
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kernel import DEFAULT_TIMEOUT_SECONDS, PythonKernel  # noqa: E402

SOCKET_PATH = os.environ.get("SANDBOX_SOCKET_PATH", "/tmp/kernel.sock")
TIMEOUT_SECONDS = float(os.environ.get("SANDBOX_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS))

kernel = PythonKernel(timeout_seconds=TIMEOUT_SECONDS)


def _to_jsonable(value: object) -> object:
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {k: _to_jsonable(v) for k, v in dataclasses.asdict(value).items()}
    if isinstance(value, list):
        return [_to_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {k: _to_jsonable(v) for k, v in value.items()}
    return value


class KernelRequestHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        try:
            raw = self.rfile.readline()
            if not raw:
                return
            request = json.loads(raw.decode("utf-8"))
            response = self._dispatch(request)
        except Exception as exc:  # noqa: BLE001 — never let a bad request kill the server
            response = {"status": "server_error", "message": f"{type(exc).__name__}: {exc}"}
        self.wfile.write((json.dumps(response) + "\n").encode("utf-8"))

    def _dispatch(self, request: dict) -> dict:
        action = request.get("action")
        if action == "ping":
            return {"status": "pong"}
        if action == "restart":
            kernel.restart()
            return {"status": "restarted"}
        if action == "execute":
            code = request.get("code", "")
            result = kernel.execute(code)
            return {"status": "ok", "result": _to_jsonable(result)}
        return {"status": "unknown_action", "action": action}


class UnixSocketServer(socketserver.UnixStreamServer):
    allow_reuse_address = True


def main() -> None:
    if os.path.exists(SOCKET_PATH):
        os.remove(SOCKET_PATH)
    server = UnixSocketServer(SOCKET_PATH, KernelRequestHandler)
    os.chmod(SOCKET_PATH, 0o600)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        if os.path.exists(SOCKET_PATH):
            os.remove(SOCKET_PATH)


if __name__ == "__main__":
    # socketserver's default family is AF_INET; UnixStreamServer needs AF_UNIX,
    # which it already sets — this import just documents the dependency clearly.
    assert hasattr(socket, "AF_UNIX"), "the sandbox image must run on a POSIX host (Linux container)"
    main()
