# syntax=docker/dockerfile:1.7
FROM mambaorg/micromamba:1.5.0

ARG PYTHON_VERSION=3.12
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

ENTRYPOINT ["uv", "run", "hotpass"]
CMD ["--help"]
