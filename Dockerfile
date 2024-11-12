FROM python:3.12-slim

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get -y upgrade \
    && apt-get install --no-install-recommends -y \
        gcc \
        g++ \
        locales \
        curl \
        xz-utils \
        ca-certificates \
        openssl \
        make \
        git \
        pkg-config \
    && curl -o /usr/local/share/ca-certificates/ca_bundle.crt https://storage.botifyme.dev/apps/nats/ca_bundle.crt \
    && chmod 644 /usr/local/share/ca-certificates/ca_bundle.crt \
    && update-ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /usr/share/doc/* \
    && rm -rf /usr/share/man/*

  
# Install uv and set up Python dependencies in one layer
WORKDIR /usr/src/app
COPY requirements.lock pyproject.toml README.md ./
RUN pip install uv \
    && uv pip install --system -r requirements.lock \
    && uv pip install --system -U agentifyme

# Start of Selection
ARG AGENTIFYME_PYTHON_WORKER_VERSION
ARG AGENTIFYME_WORKER_VERSION
ENV AGENTIFYME_WORKER_VERSION=${AGENTIFYME_WORKER_VERSION} \
  AGENTIFYME_PYTHON_WORKER_VERSION=${AGENTIFYME_PYTHON_WORKER_VERSION}

RUN if [ ! -z "${AGENTIFYME_PYTHON_WORKER_VERSION}" ]; then \
    curl -L https://agentifyme.ai/install-py-worker.sh | bash \
    fi \
    && if [ ! -z "${AGENTIFYME_WORKER_VERSION}" ]; then \
    curl -L https://agentifyme.ai/install-worker.sh | bash \
    fi


COPY src/ ./src
COPY prompts/ ./prompts
COPY agentifyme.yml ./
COPY .agentifyme/project.app ./.agentifyme/project.app 

CMD ["/usr/local/bin/agentifyme-worker"]
