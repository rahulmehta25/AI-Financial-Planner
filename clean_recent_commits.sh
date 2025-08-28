#!/bin/bash

# Clean Claude references from recent commits using interactive rebase
echo "Cleaning Claude references from recent commits..."

# Get the current branch
CURRENT_BRANCH=$(git branch --show-current)

# Create backup
git branch "backup-${CURRENT_BRANCH}-$(date +%Y%m%d-%H%M%S)"

# Use git rebase to edit the last 20 commits
# We'll use a sequence of commands to automate the message editing
EDITOR="sed -i.bak -e '/Generated with Claude Code/d' -e '/Co-Authored-By: Claude/d' -e '/noreply@anthropic.com/d' -e 's/🤖 //g'" \
git rebase -i HEAD~20 --exec 'git commit --amend --no-edit -m "$(git log --format=%B -n1 | sed -e "/Generated with Claude Code/d" -e "/Co-Authored-By: Claude/d" -e "/noreply@anthropic.com/d" -e "s/🤖 //g" | grep -v "^$")"'

echo "Cleanup complete!"
echo "Review the changes with: git log --oneline -20"