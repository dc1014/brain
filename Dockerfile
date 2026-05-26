FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    unzip \
    && rm -rf /var/lib/apt/lists/*

ENV DENO_INSTALL="/root/.deno"
RUN curl -fsSL https://deno.land/install.sh | sh
ENV PATH="$DENO_INSTALL/bin:$PATH"

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Explicit environment variable to insulate container orchestration
ENV CORETEX_CONTAINER_TRACK="1"

WORKDIR /opt/coretex

# Copy configuration along with documentation to pass metadata validation
COPY pyproject.toml README.md ./
COPY Sense/pyproject.toml Sense/README.md ./Sense/

RUN uv pip install --system -e .
RUN uv pip install --system -e ./Sense

COPY . .

ENTRYPOINT ["python", "-m", "System.cli"]
