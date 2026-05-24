FROM python:3.12-slim-bookworm

# Install base UNIX utilities and Playwright/Deno dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Deno (For the secure WASM Agentic execution sandbox)
ENV DENO_INSTALL="/root/.deno"
RUN curl -fsSL https://deno.land/install.sh | sh
ENV PATH="$DENO_INSTALL/bin:$PATH"

# Install Astral's 'uv' for lightning-fast Python dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /opt/brain

# Copy dependency manifests first to leverage Docker layer caching
COPY pyproject.toml .
COPY Sense/pyproject.toml ./Sense/

# Install dependencies using uv into the system environment inside the container
RUN uv pip install --system -e .
RUN uv pip install --system -e ./Sense

# Copy the rest of the OS framework
COPY . .

# ⚡ FIXED: Eradicated divergent script execution references, pointing directly to the `brain` file
RUN chmod +x /opt/brain/brain

ENTRYPOINT ["python", "-m", "System.cli"]
