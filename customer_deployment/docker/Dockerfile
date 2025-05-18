# Dockerfile.enterprise
FROM nvidia/cuda:12.2.0-base-ubuntu22.04 AS builder

# Secure build environment
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    build-essential \
    libssl-dev \
    tpm2-tools \
    && rm -rf /var/lib/apt/lists/*

# Create protected environment
RUN python3.11 -m venv /opt/quantumml && \
    chmod 755 /opt/quantumml

# Install compiled dependencies (obfuscated)
COPY --chown=root:root ./compiled_deps /tmp/compiled_deps
RUN pip install --no-index --find-links=/tmp/compiled_deps \
    quantumml-core==1.0.0 \
    qsecure==2.3.1 \
    && rm -rf /tmp/compiled_deps

# Final image
FROM nvidia/cuda:12.2.0-base-ubuntu22.04
COPY --from=builder /opt/quantumml /opt/quantumml

# Hardware security
COPY tpm-provision /usr/local/bin/
RUN chmod 755 /usr/local/bin/tpm-provision

# License enforcement
COPY license-check /usr/local/bin/
RUN chmod 700 /usr/local/bin/license-check

# Obfuscated entrypoint
COPY --chown=root:root entrypoint.sh /opt/
RUN chmod 755 /opt/entrypoint.sh && \
    strip /opt/entrypoint.sh

# Runtime environment
ENV PATH="/opt/quantumml/bin:$PATH"
WORKDIR /app
VOLUME ["/data"]
EXPOSE 8080/tcp

# Quantum-safe init
ENTRYPOINT ["/opt/entrypoint.sh"]