#!/usr/bin/env bash
# ==============================================================================
# Tapis Dataset Copy / Transfer Script
# Non-destructive copy from source Tapis system to destination Tapis system
# ==============================================================================
set -euo pipefail

# 1. Configuration (Edit these or pass as environment variables)
TAPIS_BASE_URL="${TAPIS_BASE_URL:-https://icicleai.tapis.io}"
SOURCE_SYSTEM="${SOURCE_SYSTEM:-source_system_id}"
SOURCE_PATH="${SOURCE_PATH:-/path/to/source/dataset}"
DEST_SYSTEM="${DEST_SYSTEM:-digitalagedustorage}"
DEST_PATH="${DEST_PATH:-/datasets/skin_cancer}"
TAPIS_JWT="${TAPIS_JWT:-}"

if [ -z "$TAPIS_JWT" ]; then
    echo "[ERROR] TAPIS_JWT is required. Export it with: export TAPIS_JWT='...'"
    exit 1
fi

SOURCE_URI="tapis://${SOURCE_SYSTEM}/${SOURCE_PATH#/}"
DEST_URI="tapis://${DEST_SYSTEM}/${DEST_PATH#/}"

echo "=================================================="
echo "Initiating Tapis Background Copy Task..."
echo "Source:      ${SOURCE_URI}"
echo "Destination: ${DEST_URI}"
echo "=================================================="

# 2. Submit Transfer Task
RESPONSE=$(curl -s -S -X POST "${TAPIS_BASE_URL}/v3/files/transfers" \
  -H "X-Tapis-Token: ${TAPIS_JWT}" \
  -H "Content-Type: application/json" \
  -d '{
    "tag": "dataset-copy",
    "elements": [
      {
        "sourceURI": "'"${SOURCE_URI}"'",
        "destinationURI": "'"${DEST_URI}"'"
      }
    ]
  }')

echo "Response: ${RESPONSE}"

TASK_UUID=$(python3 -c "import json; data=json.loads('''${RESPONSE}'''); print(data.get('result', {}).get('uuid', ''))" 2>/dev/null || true)

if [ -z "$TASK_UUID" ]; then
    echo "[ERROR] Failed to extract transfer task UUID from response."
    exit 1
fi

echo "[SUCCESS] Transfer task submitted! UUID: ${TASK_UUID}"
echo "[INFO] Monitoring transfer status (Press Ctrl+C to stop polling; task continues in background)..."

# 3. Monitor Status
while true; do
    STATUS_RESP=$(curl -s -S -X GET "${TAPIS_BASE_URL}/v3/files/transfers/${TASK_UUID}" \
      -H "X-Tapis-Token: ${TAPIS_JWT}" \
      -H "Content-Type: application/json")

    STATUS=$(python3 -c "import json; data=json.loads('''${STATUS_RESP}'''); print(data.get('result', {}).get('status', 'UNKNOWN'))" 2>/dev/null || echo "UNKNOWN")
    TRANSFERRED=$(python3 -c "import json; data=json.loads('''${STATUS_RESP}'''); print(data.get('result', {}).get('bytesTransferred', 0))" 2>/dev/null || echo "0")
    TOTAL=$(python3 -c "import json; data=json.loads('''${STATUS_RESP}'''); print(data.get('result', {}).get('totalBytes', 0))" 2>/dev/null || echo "0")

    echo "[$(date +'%H:%M:%S')] Transfer Status: ${STATUS} (${TRANSFERRED}/${TOTAL} bytes)"

    if [ "$STATUS" = "COMPLETED" ] || [ "$STATUS" = "FINISHED" ]; then
        echo "[SUCCESS] Dataset transfer completed successfully!"
        break
    elif [ "$STATUS" = "FAILED" ] || [ "$STATUS" = "CANCELLED" ] || [ "$STATUS" = "ERROR" ]; then
        echo "[ERROR] Dataset transfer failed with status: ${STATUS}"
        exit 1
    fi
    sleep 5
done
