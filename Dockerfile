ARG PYTHON_VERSION=3.12-slim-bookworm

FROM python:${PYTHON_VERSION}

LABEL maintainer="AgentifyMe <info@agentifyme.ai>, @arunreddy"
LABEL description="Docker image for executing python functions using AgentifyMe CLI"
LABEL org.opencontainers.image.source="https://github.com/agentifyme/agentifyme-py"
LABEL version=0.1.0

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install runtime packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd -m -s /bin/bash agnt5

# Set working directory
WORKDIR /home/agnt5/app
RUN chown agnt5:agnt5 /home/agnt5/app

USER agnt5

RUN curl -LsSf https://astral.sh/uv/install.sh | bash
RUN curl -LsSf https://agentifyme.ai/cli.sh | bash
RUN curl -LsSf "https://agentifyme.ai/init-py.sh?$(date +%s)" | bash


ENV PATH="${PATH}:/home/agnt5/.local/bin:/home/agnt5/app/.venv/bin:/home/agnt5/.agentifyme/bin"

RUN uv venv

COPY --chown=agnt5:agnt5  README.md .
COPY --chown=agnt5:agnt5  pyproject.toml .
COPY --chown=agnt5:agnt5  uv.lock .
RUN uv sync

COPY --chown=agnt5:agnt5  src src
COPY --chown=agnt5:agnt5 agentifyme.yml .

RUN uv add agentifyme --extra grpc --extra worker

CMD ["/home/agnt5/.agentifyme/bin/agnt5-init"]
