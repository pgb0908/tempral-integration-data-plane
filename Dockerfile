FROM python:3.11-slim

WORKDIR /app

# Copy dependency metadata first for layer caching
COPY pyproject.toml ./

# Create a stub package so editable install works before full source is copied
RUN mkdir -p flow_engine && touch flow_engine/__init__.py

# Install package and dependencies
RUN pip install --no-cache-dir -e .

# Copy actual source code
COPY . .

# Ensure flows directory exists for file-based storage
RUN mkdir -p flows

EXPOSE 8000

CMD ["python", "main.py", "both"]
