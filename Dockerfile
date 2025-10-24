# syntax=docker/dockerfile:1.7
FROM mambaorg/micromamba:2.3.2

ARG PYTHON_VERSION=3.13
ENV PATH="/root/.local/bin:${PATH}"

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN micromamba install -y -n base "python=${PYTHON_VERSION}" -c conda-forge \
    && micromamba clean --all --yes

RUN curl -LsSf https://astral.sh/uv/install.sh | sh

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
