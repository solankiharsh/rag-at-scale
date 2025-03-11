# Use your target base image with Poetry pre-installed
FROM docker.target.com/app/tgt-python-poetry:3.11-debian-slim-bookworm

# Install supervisor, curl (for runtime-connector), and poppler-utils (for pdf2image)
RUN apt-get update -qq && \
    apt-get install -y supervisor poppler-utils curl

# Install runtime-connector
ENV RUNTIME_VERSION=v2.4.6
RUN cd / && \
    curl -sk "https://binrepo.target.com/artifactory/platform/runtime-connector/${RUNTIME_VERSION}/runtime-connector-linux-amd64-${RUNTIME_VERSION}.tgz" \
    | tar -C / -xvzf -

# Copy your project files
COPY . ./

# Disable Poetry virtualenv creation so that dependencies are installed into the system environment
RUN poetry config virtualenvs.create false

# (Optional) Clear Poetry cache to remove any old cached files that might conflict
# RUN poetry cache clear --all pypi

# Install dependencies via Poetry (without dev dependencies)
RUN poetry install --no-interaction --no-ansi

# Copy Supervisor configuration (ensure your supervisord.conf defines your processes)
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose the ports you need (e.g., 8000 for FastAPI and 5555 for Flower)
EXPOSE 8000 5555

# Use runtime-connector to run the entrypoint that launches supervisor (which then starts uvicorn, celery, etc.)
ENTRYPOINT ["/runtime-connector", "--", "/bin/sh", "./entrypoint.sh"]

# Labels for metadata
LABEL version="1.0" \
      author="Z0084K9" \
      maintainer="Harsh Solanki <Harsh.Solanki@target.com>"
