# syntax=docker/dockerfile:1.19
FROM mambaorg/micromamba:2.3.2

ARG PYTHON_VERSION=3.13
ENV PATH="/root/.local/bin:${PATH}"

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN micromamba install -y -n base "python=${PYTHON_VERSION}" -c conda-forge \
    && micromamba clean --all --yes

ARG UV_VERSION=0.9.5
ARG UV_SHA256=2cf10babba653310606f8b49876cfb679928669e7ddaa1fb41fb00ce73e64f66
RUN curl -LsSf -o /tmp/uv.tar.gz "https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/uv-x86_64-unknown-linux-gnu.tar.gz" \
    && echo "${UV_SHA256}  /tmp/uv.tar.gz" | sha256sum -c - \
    && tar -xzf /tmp/uv.tar.gz -C /usr/local/bin --strip-components=1 \
        uv-x86_64-unknown-linux-gnu/uv \
        uv-x86_64-unknown-linux-gnu/uvx \
    && chmod +x /usr/local/bin/uv /usr/local/bin/uvx \
    && rm /tmp/uv.tar.gz

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen

COPY src ./src
COPY scripts ./scripts
COPY docs ./docs
COPY README.md ./

# Create a non-root user and switch to it
RUN useradd --create-home appuser
USER appuser

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl --fail http://localhost:8000/health || exit 1

ENTRYPOINT ["uv", "run", "hotpass"]
CMD ["--help"]
