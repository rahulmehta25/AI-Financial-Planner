#!/bin/bash

# Automated script to remove Claude references from commit messages
set -e

echo "Starting automated cleanup of Claude references..."

# Create backup
BACKUP_BRANCH="backup-$(date +%Y%m%d-%H%M%S)"
git branch $BACKUP_BRANCH
echo "Created backup branch: $BACKUP_BRANCH"

# Function to clean a commit message
clean_commit_message() {
    local commit=$1
    local msg=$(git log --format=%B -n1 $commit | \
        grep -v "Generated with Claude Code" | \
        grep -v "Co-Authored-By: Claude" | \
        grep -v "noreply@anthropic.com" | \
        sed 's/🤖 //g' | \
        grep -v "^\s*$" || true)
    
    if [ -z "$msg" ]; then
        # If message becomes empty, use original subject line
        msg=$(git log --format=%s -n1 $commit)
    fi
    
    echo "$msg"
}

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)

# Export the function for use in git filter-branch
export -f clean_commit_message

# Use filter-branch with proper warning suppression
FILTER_BRANCH_SQUELCH_WARNING=1 git filter-branch -f --msg-filter '
    grep -v "Generated with Claude Code" | \
    grep -v "Co-Authored-By: Claude" | \
    grep -v "noreply@anthropic.com" | \
    sed "s/🤖 //g" | \
    grep -v "^[[:space:]]*$" || cat
' HEAD~30..HEAD

echo ""
echo "Cleanup complete!"
echo "Review changes with: git log --oneline -20"
echo ""
echo "To push changes (THIS WILL REWRITE HISTORY):"
echo "  git push --force-with-lease origin $CURRENT_BRANCH"
echo ""
echo "To restore from backup if needed:"
echo "  git reset --hard $BACKUP_BRANCH"