#!/usr/bin/env python3
"""
Script to remove Claude references from git commit messages
"""
import subprocess
import sys
import re

def get_commit_message(commit_hash):
    """Get the full commit message for a given hash."""
    result = subprocess.run(
        ['git', 'show', '--format=%B', '-s', commit_hash],
        capture_output=True,
        text=True
    )
    return result.stdout

def clean_message(message):
    """Remove Claude references from commit message."""
    # Remove lines containing Claude references
    lines = message.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Skip lines with Claude references
        if any(phrase in line for phrase in [
            'Generated with Claude Code',
            'Co-Authored-By: Claude',
            'noreply@anthropic.com',
            '[Claude Code]'
        ]):
            continue
        # Remove robot emoji
        line = line.replace('🤖 ', '')
        # Keep the line if it has content
        if line.strip():
            cleaned_lines.append(line)
    
    # Join and clean up extra blank lines
    cleaned = '\n'.join(cleaned_lines)
    # Remove multiple consecutive newlines
    cleaned = re.sub(r'\n\n+', '\n\n', cleaned)
    return cleaned.strip()

def main():
    print("Creating backup branch...")
    subprocess.run(['git', 'branch', 'backup-before-cleanup'])
    
    # Get the last 30 commits
    result = subprocess.run(
        ['git', 'log', '--format=%H', '-30'],
        capture_output=True,
        text=True
    )
    commits = result.stdout.strip().split('\n')
    
    print(f"Processing {len(commits)} commits...")
    
    # Start interactive rebase
    oldest_commit = commits[-1]
    
    # Create a rebase todo file
    with open('.git/rebase-todo', 'w') as f:
        for commit in commits[:-1]:
            f.write(f"edit {commit[:7]}\n")
    
    print("\nTo clean the commits, run these commands manually:")
    print("1. Start interactive rebase:")
    print(f"   git rebase -i {oldest_commit}^")
    print("\n2. Change all 'pick' to 'edit' in the editor")
    print("\n3. For each commit, run:")
    print("   python3 remove_claude_from_commits.py --amend")
    print("   git rebase --continue")
    print("\n4. When done, force push:")
    print("   git push --force-with-lease origin feature/complete-financial-planning-system")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--amend':
        # Get current commit message
        message = subprocess.run(
            ['git', 'log', '--format=%B', '-n1'],
            capture_output=True,
            text=True
        ).stdout
        
        # Clean it
        cleaned = clean_message(message)
        
        # Write to temp file
        with open('/tmp/commit_msg_clean.txt', 'w') as f:
            f.write(cleaned)
        
        # Amend the commit
        subprocess.run(['git', 'commit', '--amend', '-F', '/tmp/commit_msg_clean.txt'])
        print("Commit message cleaned!")
    else:
        main()