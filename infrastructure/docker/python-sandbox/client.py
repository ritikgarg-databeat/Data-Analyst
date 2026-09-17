"""Invoked via `docker exec <container> python /sandbox/client.py <action> [<base64-code>]`
from the host side (see `app/python_lab/docker_backend.py`). Connects to the
kernel's Unix socket *from inside the container*, relays one request, prints
the JSON response to stdout, and exits — `docker exec`'s own stdout capture
is the entire transport back to the host, so this script must print exactly
one line and nothing else (no logging to stdout).
"""

from __future__ import annotations

import base64
import json
import os
import socket
import sys

SOCKET_PATH = os.environ.get("SANDBOX_SOCKET_PATH", "/tmp/kernel.sock")
# Give the socket read a bit more headroom than the kernel's own execution
# timeout, so the kernel's internal SIGALRM has a chance to fire and reply
# with a proper structured timeout error before this client gives up.
READ_TIMEOUT_SECONDS = float(os.environ.get("SANDBOX_TIMEOUT_SECONDS", "10")) + 5.0


def main() -> None:
    action = sys.argv[1] if len(sys.argv) > 1 else "ping"
    request: dict[str, object] = {"action": action}
    if action == "execute":
        encoded_code = sys.argv[2] if len(sys.argv) > 2 else ""
        request["code"] = base64.b64decode(encoded_code).decode("utf-8")

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(READ_TIMEOUT_SECONDS)
    try:
        sock.connect(SOCKET_PATH)
        sock.sendall((json.dumps(request) + "\n").encode("utf-8"))
        sock.shutdown(socket.SHUT_WR)
        chunks = []
        while True:
            chunk = sock.recv(65536)
            if not chunk:
                break
            chunks.append(chunk)
        raw = b"".join(chunks)
    except (TimeoutError, OSError) as exc:
        print(json.dumps({"status": "client_error", "message": f"{type(exc).__name__}: {exc}"}))
        return
    finally:
        sock.close()

    sys.stdout.write(raw.decode("utf-8"))


if __name__ == "__main__":
    main()
