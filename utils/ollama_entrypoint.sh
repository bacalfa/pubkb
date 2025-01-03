#!/bin/sh

# Start the Ollama server in the background
ollama serve &

# Wait for the server to be ready
sleep 5

# Pull the required models
source /.env
ollama pull ${LLM_MODEL}
ollama pull ${EMBEDDING_MODEL}

# Wait for background processes to finish
wait