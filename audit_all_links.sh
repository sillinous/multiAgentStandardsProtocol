#!/bin/bash

echo "=========================================="
echo "COMPREHENSIVE DASHBOARD LINK AUDIT"
echo "=========================================="
echo

for file in src/superstandard/api/*.html; do
    filename=$(basename "$file")
    echo "=========================================="
    echo "FILE: $filename"
    echo "=========================================="

    echo
    echo "--- Navigation <a href> Links ---"
    grep -n 'href=' "$file" | grep -v 'stylesheet' | grep -v 'http://' | grep -v 'https://' | head -20

    echo
    echo "--- JavaScript onclick Redirects ---"
    grep -n "window.location.href=" "$file" | head -20

    echo
    echo "--- onclick Modal Opens ---"
    grep -n 'onclick="openModal' "$file" | head -10

    echo
    echo
done
