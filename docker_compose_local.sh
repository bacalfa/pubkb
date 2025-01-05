export LLM_MODEL=llama3:8b
echo "LLM_MODEL=${LLM_MODEL}" > .env
export EMBEDDING_MODEL=nomic-embed-text
echo "EMBEDDING_MODEL=${EMBEDDING_MODEL}" >> .env
export BASE_URL=http://host.docker.internal:11434
echo "BASE_URL=${BASE_URL}" >> .env
export REDIS_URL=redis://host.docker.internal:6379
echo "REDIS_URL=${REDIS_URL}" >> .env

docker compose -f compose_local.yaml up --build