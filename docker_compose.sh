export LLM_MODEL=llama3:8b
echo "LLM_MODEL=${LLM_MODEL}" > .env
export EMBEDDING_MODEL=nomic-embed-text
echo "EMBEDDING_MODEL=${EMBEDDING_MODEL}" >> .env
export BASE_URL=http://ollama:11434
echo "BASE_URL=${BASE_URL}" >> .env
export REDIS_URL=http://redis:6379
echo "REDIS_URL=${REDIS_URL}" >> .env

docker compose -f compose.yaml up --build