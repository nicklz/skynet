#!/bin/bash

# Build the Docker image
echo "Building Docker image..."
docker build -t my-selenium-script .

# Define the volume path on the host and inside the container
HOST_VOLUME_PATH="./data"  # Adjust this path as needed
CONTAINER_VOLUME_PATH="/usr/src/app/data"

# Create the host directory if it doesn't exist
mkdir -p "$HOST_VOLUME_PATH"

# Check if a prompt argument is provided
if [ -z "$1" ]; then
  echo "No prompt provided. Using default prompt."
  PROMPT="hello, what are you doing?"
else
  PROMPT="$1"
fi

# Run the Docker container with volume and pass the prompt argument
echo "Running Docker container with prompt: '$PROMPT'..."
docker run --rm \
  -v "$HOST_VOLUME_PATH:$CONTAINER_VOLUME_PATH" \
  my-selenium-script "$PROMPT"

# Optional: Clean up or additional commands can be added here
