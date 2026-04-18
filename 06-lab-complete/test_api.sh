#!/bin/bash
# hãy di chuyển tới branch MASTER
# Script to test the AI Agent API (Bash)

API_KEY="lab6-secret-key-123"
BASE_URL="http://localhost:8000"

echo "1. Testing Health Check (Public)"
curl -X GET "$BASE_URL/health" -v
echo -e "\n"

echo "2. Testing Readiness Probe (Public)"
curl -X GET "$BASE_URL/ready" -v
echo -e "\n"

echo "3. Testing AI Agent Ask (Protected)"
curl -X POST "$BASE_URL/ask" \
     -H "Content-Type: application/json" \
     -H "X-API-Key: $API_KEY" \
     -d '{"question": "How do I deploy a docker container?"}'
echo -e "\n"

echo "4. Testing Metrics (Protected)"
curl -X GET "$BASE_URL/metrics" \
     -H "X-API-Key: $API_KEY"
echo -e "\n"

echo "5. Testing Unauthorized Request"
curl -X GET "$BASE_URL/metrics"
echo -e "\n"
