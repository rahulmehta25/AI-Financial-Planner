#!/bin/bash

# Read the utils function
UTILS_CONTENT='import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}'

# Process each UI component file
for file in src/components/ui/*.tsx; do
  if [ -f "$file" ]; then
    echo "Processing $file"
    
    # Create a temporary file with the inlined utils
    temp_file="${file}.tmp"
    
    # Remove the utils import line and add the imports and function at the top
    sed '/import.*utils/d' "$file" > "$temp_file"
    
    # Add the necessary imports at the top if not already present
    if ! grep -q "import { type ClassValue, clsx }" "$temp_file"; then
      # Insert the imports and function after the first import or at the beginning
      awk '
        BEGIN { printed = 0 }
        /^import/ && !printed { 
          print "import { type ClassValue, clsx } from \"clsx\""
          print "import { twMerge } from \"tailwind-merge\""
          print ""
          print "function cn(...inputs: ClassValue[]) {"
          print "  return twMerge(clsx(inputs))"
          print "}"
          print ""
          printed = 1
        }
        { print }
      ' "$temp_file" > "${temp_file}.2"
      mv "${temp_file}.2" "$temp_file"
    fi
    
    # Move the temp file back
    mv "$temp_file" "$file"
  fi
done

echo "All UI components updated with inlined cn function"
