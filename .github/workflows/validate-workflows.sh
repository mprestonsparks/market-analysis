#!/bin/bash

# Validate GitHub workflow files
for file in .github/workflows/*.yml; do
    echo "Validating $file..."
    if ! gh workflow view "$file" >/dev/null 2>&1; then
        echo "Error in $file"
        exit 1
    fi
done

echo "All workflow files are valid!"
exit 0
