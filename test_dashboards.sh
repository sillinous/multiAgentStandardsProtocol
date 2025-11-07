#!/bin/bash

echo "Testing all dashboard endpoints..."
echo

for page in user admin network coordination consciousness; do
    echo "========================================"
    echo "Testing /dashboard/$page"
    echo "========================================"
    response=$(curl -s -w "\nHTTP_CODE:%{http_code}" http://localhost:8080/dashboard/$page)
    http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)
    content_length=$(echo "$response" | grep -v "HTTP_CODE:" | wc -c)
    echo "Status: $http_code"
    echo "Content length: $content_length bytes"
    if [ "$http_code" -eq 200 ]; then
        echo "✅ SUCCESS"
    else
        echo "❌ FAILED"
        echo "$response" | grep -v "HTTP_CODE:"
    fi
    echo
done
