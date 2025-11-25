FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    libffi-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /install

COPY pyproject.toml README.md ./
COPY src ./src

RUN python -m venv /opt/lcc \
    && /opt/lcc/bin/pip install --upgrade pip \
    && /opt/lcc/bin/pip install .

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LCC_CACHE_DIR=/var/cache/lcc \
    PASSLIB_MAX_PASSWORD_SIZE=4096

# Install git for cloning repositories
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r lcc && useradd -r -g lcc lcc \
    && mkdir -p ${LCC_CACHE_DIR} /workspace /var/lib/lcc \
    && chown -R lcc:lcc ${LCC_CACHE_DIR} /workspace /var/lib/lcc

COPY --from=builder /opt/lcc /opt/lcc

USER lcc
WORKDIR /workspace

ENV PATH="/opt/lcc/bin:$PATH"
ENV PYTHONPATH="/opt/lcc/lib/python3.11/site-packages"

VOLUME ["/workspace", "/var/lib/lcc"]

# Default entrypoint is the CLI
ENTRYPOINT ["lcc"]
CMD ["--help"]

HEALTHCHECK --interval=1m --timeout=10s --start-period=30s --retries=3 \
    CMD lcc --version || exit 1
