# Python Lab sandbox image — the ONLY place submitted Python code actually
# runs. Never built into or run by the `api` image/process; the FastAPI app
# only ever talks to a running container of THIS image via `docker exec`
# (see app/python_lab/docker_backend.py). See docs/architecture.md#python-lab-phase-4
# for the full isolation design (network_mode=none, resource limits,
# read-only root filesystem, non-root user, dropped capabilities).

FROM python:3.12-slim

# Prevents .pyc write attempts and stdout buffering surprises; MPLBACKEND is
# a second line of defense alongside kernel.py's own explicit matplotlib.use("Agg").
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLBACKEND=Agg

WORKDIR /sandbox

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY kernel.py server.py client.py ./

# Non-root, no home directory writes needed — the container's root filesystem
# is mounted read-only at runtime (see docker_backend.py); only /tmp (tmpfs)
# and the read-only /data dataset mount are writable/reachable.
RUN useradd --no-create-home --uid 1000 sandbox
USER sandbox

ENTRYPOINT ["python", "/sandbox/server.py"]
