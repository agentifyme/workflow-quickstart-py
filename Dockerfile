ARG RUNTIME_VERSION=0.2
ARG PYTHON_VERSION=3.13
FROM ghcr.io/agentifyme/python-runtime:${RUNTIME_VERSION}-python${PYTHON_VERSION}

COPY --chown=agnt5:agnt5  README.md .
COPY --chown=agnt5:agnt5  pyproject.toml .
COPY --chown=agnt5:agnt5  uv.lock .
RUN uv sync

RUN uv pip install agentifyme[grpc,worker]

COPY --chown=agnt5:agnt5  src src
COPY --chown=agnt5:agnt5 agentifyme.yml .

