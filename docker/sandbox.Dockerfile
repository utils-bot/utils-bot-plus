# Sandbox Execution Docker Images
# These images provide secure environments for code execution

FROM python:3.11-alpine as python-sandbox

# Install system dependencies for common packages
RUN apk add --no-cache \
    gcc \
    musl-dev \
    linux-headers \
    && rm -rf /var/cache/apk/*

# Create non-root user
RUN adduser -D -s /bin/sh sandbox

# Install common Python packages for competitive programming
RUN pip install --no-cache-dir \
    numpy \
    scipy \
    matplotlib \
    sympy \
    networkx \
    && rm -rf /root/.cache/pip

# Set working directory
WORKDIR /app

# Switch to non-root user
USER sandbox

# Default command
CMD ["python", "-u", "main.py"]

# ---

FROM gcc:11-alpine as cpp-sandbox

# Install additional tools
RUN apk add --no-cache \
    make \
    cmake \
    && rm -rf /var/cache/apk/*

# Create non-root user
RUN adduser -D -s /bin/sh sandbox

WORKDIR /app
USER sandbox

CMD ["sh", "-c", "g++ -o solution main.cpp && ./solution"]

# ---

FROM openjdk:17-alpine as java-sandbox

# Create non-root user
RUN adduser -D -s /bin/sh sandbox

WORKDIR /app
USER sandbox

CMD ["sh", "-c", "javac Main.java && java Main"]
