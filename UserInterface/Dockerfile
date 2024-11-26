# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install necessary build tools and libraries for pyodbc
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    unixodbc-dev

# Install the necessary dependencies, including python-dotenv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the .env file to the container
COPY .env .env

# Copy the rest of the application code
COPY . .

# Accept the GCP Service Account file path as a build argument
ARG GCP_SERVICE_ACCOUNT_FILE

# Print out the value of the GCP_SERVICE_ACCOUNT_FILE to verify
RUN echo "GCP Service Account File: ${GCP_SERVICE_ACCOUNT_FILE}"

# Copy the GCP JSON key file from the build argument to the container
COPY ${GCP_SERVICE_ACCOUNT_FILE} /app/docker2gcp-b80ec434f87f.json

# Set environment variable for the GCP key file
ENV GCP_SERVICE_ACCOUNT_FILE=/app/docker2gcp-b80ec434f87f.json

# Command to run the application
CMD ["python", "app.py"]
