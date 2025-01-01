docker compose -f compose.yaml up --build

# Download models to ollama service
bash utils/download_llm.sh ${LLM_MODEL}  # LLM
bash utils/download_llm.sh ${EMBEDDING_MODEL}  # Embedding