#!/bin/bash

# Script to remove Claude references from git history
# WARNING: This will rewrite git history

echo "This script will rewrite git history to remove Claude references."
echo "Make sure you have a backup of your repository!"
echo "Press Ctrl+C to cancel, or Enter to continue..."
read

# Create a backup branch first
git branch backup-before-claude-cleanup

# Use git filter-branch to remove Claude references from commit messages
git filter-branch --force --msg-filter '
    sed -e "/Generated with Claude Code/d" \
        -e "/🤖 Generated with \\[Claude Code\\]/d" \
        -e "/Co-Authored-By: Claude/d" \
        -e "/noreply@anthropic.com/d" \
        -e "s/Claude Code//g" \
        -e "s/🤖 //g" \
        -e "/^[[:space:]]*$/d"
' --tag-name-filter cat -- --all

echo "Cleanup complete!"
echo "To push the changes, you'll need to force push:"
echo "git push --force-with-lease origin feature/complete-financial-planning-system"
echo ""
echo "If something went wrong, you can restore from backup:"
echo "git reset --hard backup-before-claude-cleanup"