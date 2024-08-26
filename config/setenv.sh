#!/bin/bash

while IFS= read -r line || [[ -n "$line" ]]; do
    if [[ $line =~ ^#.*$ ]]; then
        continue  # Skip comments
    fi
    if [[ -n $line ]]; then
        export "$line"
    fi
done < config/.env