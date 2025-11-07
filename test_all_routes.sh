#!/bin/bash

echo "=========================================="
echo "Testing All Dashboard Routes"
echo "=========================================="
echo

routes=(
    "/dashboard/user"
    "/dashboard/admin"
    "/dashboard/network"
    "/dashboard/coordination"
    "/dashboard/consciousness"
    "/docs"
)

echo "Testing ${#routes[@]} unique routes..."
echo

passed=0
failed=0

for route in "${routes[@]}"; do
    status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080$route)

    if [ "$status" = "200" ]; then
        echo "✅ $route → $status OK"
        ((passed++))
    else
        echo "❌ $route → $status FAILED"
        ((failed++))
    fi
done

echo
echo "=========================================="
echo "Results: $passed passed, $failed failed"
echo "=========================================="

if [ $failed -eq 0 ]; then
    echo "✅ ALL ROUTES WORKING!"
    exit 0
else
    echo "❌ Some routes failed"
    exit 1
fi
