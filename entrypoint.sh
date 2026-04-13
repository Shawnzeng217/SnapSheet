#!/bin/sh
# Entrypoint for Hotel OCR container
# Initializes persistent data directory if DATA_DIR is set (e.g. Render disk)

if [ -n "$DATA_DIR" ]; then
    echo "Initializing data directory: $DATA_DIR"
    mkdir -p "$DATA_DIR/uploads" "$DATA_DIR/output" "$DATA_DIR/templates"

    # Copy default templates if templates dir is empty
    if [ -z "$(ls -A "$DATA_DIR/templates" 2>/dev/null)" ]; then
        echo "Copying default templates..."
        cp -r /app/_templates_default/* "$DATA_DIR/templates/" 2>/dev/null || true
    fi
fi

exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
