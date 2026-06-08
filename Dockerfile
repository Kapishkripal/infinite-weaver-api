# Use the official Python 3.10 slim image for a smaller footprint
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
# (The .dockerignore file ensures .env and local caches are ignored)
COPY . .

# Expose the port that Uvicorn will listen on
EXPOSE 8000

# Command to run the FastAPI server
# We bind to 0.0.0.0 so the container is accessible from the outside
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
