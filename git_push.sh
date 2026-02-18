#!/bin/bash
# JEBAT - Git Setup and Push Script
# This script prepares and pushes JEBAT to GitHub

set -e  # Exit on error

echo "🗡️  JEBAT - Git Setup & Push Script"
echo "===================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

# Check if git is installed
if ! command -v git &> /dev/null; then
    print_error "Git is not installed. Please install git first."
    echo "Download from: https://git-scm.com/"
    exit 1
fi
print_success "Git is installed"

# Check if we're in a git repository
if [ ! -d .git ]; then
    print_info "Initializing git repository..."
    git init
    print_success "Git repository initialized"
fi

# Configure git (if not already configured)
if [ -z "$(git config user.name)" ]; then
    print_info "Configuring git..."
    echo -n "Enter your GitHub username: "
    read GITHUB_USERNAME
    echo -n "Enter your email: "
    read GITHUB_EMAIL

    git config user.name "$GITHUB_USERNAME"
    git config user.email "$GITHUB_EMAIL"
    print_success "Git configured"
fi

# Check for remote
if ! git remote | grep -q "origin"; then
    print_info "Add your GitHub repository as remote:"
    echo "Example: git remote add origin https://github.com/YOUR_USERNAME/jebat-core.git"
    echo -n "Enter remote URL (or press Enter to skip): "
    read REMOTE_URL

    if [ ! -z "$REMOTE_URL" ]; then
        git remote add origin "$REMOTE_URL"
        print_success "Remote added"
    fi
fi

# Show current status
echo ""
print_info "Current git status:"
git status --short

echo ""
echo -n "Enter commit message: "
read COMMIT_MESSAGE

if [ -z "$COMMIT_MESSAGE" ]; then
    COMMIT_MESSAGE="chore: Initial JEBAT commit with complete implementation"
fi

# Add all files
print_info "Staging all files..."
git add .
print_success "Files staged"

# Commit
print_info "Committing changes..."
git commit -m "$COMMIT_MESSAGE"
print_success "Changes committed"

# Check branch
CURRENT_BRANCH=$(git branch --show-current)
print_info "Current branch: $CURRENT_BRANCH"

# Push
echo ""
print_info "Ready to push to GitHub"
echo "This will push all changes to the remote repository"
echo -n "Continue? (y/n): "
read CONFIRM

if [ "$CONFIRM" = "y" ] || [ "$CONFIRM" = "Y" ]; then
    print_info "Pushing to GitHub..."

    # Try to push
    if git push -u origin "$CURRENT_BRANCH"; then
        print_success "Successfully pushed to GitHub!"
        echo ""
        echo "🎉 JEBAT is now on GitHub!"
        echo ""
        echo "Next steps:"
        echo "1. Go to your repository on GitHub"
        echo "2. Review the files"
        echo "3. Enable GitHub Actions for CI/CD"
        echo "4. Share with the community!"
    else
        print_error "Push failed. Check your credentials and try again."
        echo ""
        echo "Troubleshooting:"
        echo "- Make sure you have write access to the repository"
        echo "- Check if you need to set up SSH keys"
        echo "- Verify the remote URL is correct"
    fi
else
    print_info "Push cancelled. You can push manually with: git push -u origin $CURRENT_BRANCH"
fi

echo ""
echo "🗡️  JEBAT - Because warriors remember everything that matters!"
