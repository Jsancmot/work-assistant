#!/bin/bash
echo "Waiting for Ollama to be ready..."
until curl -s http://ollama:11434/api/tags > /dev/null 2>&1; do
    echo "Waiting..."
    sleep 2
done

echo "Checking if model $OLLAMA_MODEL is available..."
MODELS=$(curl -s http://ollama:11434/api/tags | grep -o "\"name\":\"$OLLAMA_MODEL\"" || true)
if [ -z "$MODELS" ]; then
    echo "Downloading model $OLLAMA_MODEL..."
    OLLAMA_HOST=http://ollama:11434 ollama pull $OLLAMA_MODEL
    echo "Download complete."
else
    echo "Model $OLLAMA_MODEL already available."
fi

echo "Starting application..."
exec python -m src.main