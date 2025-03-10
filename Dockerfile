# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables for production
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies (if required, e.g., build-essential for some packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --upgrade pip && pip install poetry

# Copy only the dependency files to leverage Docker cache
COPY pyproject.toml poetry.lock* ./

# Install project dependencies (without dev dependencies)
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Copy the rest of the project
COPY . .

# Download NLTK data (punkt and averaged_perceptron_tagger)
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('averaged_perceptron_tagger')"

# Expose port 8000 for the FastAPI app
EXPOSE 8000

# Default command (overridden in docker-compose for worker)
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
