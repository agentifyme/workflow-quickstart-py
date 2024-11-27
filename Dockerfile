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
    iproute2 \
    iputils-ping \
    dnsutils \
    git \
    curl \
    ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd -m -s /bin/bash agnt5

# Set working directory
WORKDIR /home/agnt5/app
RUN chown agnt5:agnt5 /home/agnt5/app

USER agnt5

# Install Rye for the non-root userd
RUN curl -LsSf https://astral.sh/uv/install.sh | bash

ENV PATH="${PATH}:/home/agnt5/.cargo/bin:/usr/local/bin:/home/agnt5/.local/bin:/home/agnt5/app/.venv/bin"

RUN uv venv
RUN uv pip install agentifyme~=0.1.5

COPY --chown=agnt5:agnt5  README.md .
COPY --chown=agnt5:agnt5  pyproject.toml .
COPY --chown=agnt5:agnt5  requirements.lock .
RUN uv pip install -r requirements.lock

COPY --chown=agnt5:agnt5  src src
COPY --chown=agnt5:agnt5 agentifyme.yml .

CMD ["/home/agnt5/app/.venv/bin/agnt5"]