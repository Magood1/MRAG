#!/bin/bash

URL="http://127.0.0.1:8000" # Or your Azure URL
API_KEY="secret-key-123"

echo "🔥 Running Smoke Test on $URL..."

# 1. Health Check
echo -n "Checking /health... "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" $URL/health)
if [ "$STATUS" == "200" ]; then
    echo "✅ UP"
else
    echo "❌ DOWN ($STATUS)"
    exit 1
fi

# 2. Chat Endpoint (Auth Check)
echo -n "Checking Auth... "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST $URL/api/v1/assistant/chat)
if [ "$STATUS" == "403" ]; then # Expecting 403 without key
    echo "✅ Secured"
else
    echo "❌ Insecure or Error ($STATUS)"
    exit 1
fi

echo "✨ Smoke Test Passed!"