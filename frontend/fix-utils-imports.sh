#!/bin/bash

# Fix all @/lib/utils imports to use relative paths
echo "Fixing utils imports in UI components..."

# For components/ui files, they need ../../lib/utils
find src/components/ui -name "*.tsx" -o -name "*.ts" | while read file; do
  if grep -q "from ['\"]@/lib/utils" "$file"; then
    echo "Fixing $file"
    sed -i '' "s|from ['\"]@/lib/utils['\"]|from '../../lib/utils'|g" "$file"
  fi
done

echo "Done fixing imports!"