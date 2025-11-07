#!/bin/bash

echo "========================================"
echo "Testing User Control Panel API Endpoints"
echo "========================================"
echo

echo "1. GET /api/admin/stats"
echo "----------------------------------------"
response=$(curl -s http://localhost:8080/api/admin/stats)
echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
echo

echo "2. POST /api/acp/sessions (Create Session)"
echo "----------------------------------------"
response=$(curl -s -X POST http://localhost:8080/api/acp/sessions \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Session","coordination_type":"pipeline","description":"Test"}')
echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
echo

echo "3. POST /api/aconsp/collectives/main/thoughts"
echo "----------------------------------------"
response=$(curl -s -X POST http://localhost:8080/api/aconsp/collectives/main/thoughts \
  -H "Content-Type: application/json" \
  -d '{"agent_id":"test-agent","thought_type":"observation","content":"Test thought","confidence":0.9}')
echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
echo

echo "4. GET /api/anp/agents (List Agents)"
echo "----------------------------------------"
response=$(curl -s http://localhost:8080/api/anp/agents)
echo "$response" | python3 -c "import sys, json; d=json.load(sys.stdin); print(json.dumps({'success': d.get('success'), 'count': d.get('count')}, indent=2))" 2>/dev/null || echo "$response"
echo

echo "========================================"
echo "Testing WebSocket Endpoints"
echo "========================================"
echo

for ws in admin network coordination consciousness; do
    echo "WebSocket /ws/$ws: $(curl -s -I http://localhost:8080/ws/$ws 2>&1 | head -1)"
done
