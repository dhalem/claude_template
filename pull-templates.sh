#!/bin/bash
# Simple script to pull dev templates into any project
set -e

# Configuration - UPDATE THIS WITH YOUR REPO
TEMPLATES_REPO="${TEMPLATES_REPO:-https://github.com/dhalem/claude_template.git}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}📥 Pulling development templates${NC}"
echo "Repository: $TEMPLATES_REPO"
echo ""

# Create temp directory
TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT

# Clone templates
echo "Downloading templates..."
git clone --depth 1 "$TEMPLATES_REPO" "$TEMP_DIR/templates" 2>/dev/null || {
    echo -e "${YELLOW}⚠️  Could not clone $TEMPLATES_REPO${NC}"
    echo "Set TEMPLATES_REPO environment variable or edit this script"
    exit 1
}

# Simple menu
echo -e "\n${GREEN}What would you like to do?${NC}"
echo "1) Full setup (all tools)"
echo "2) Just pre-commit hooks"
echo "3) Just Python config (pyproject.toml, etc)"
echo "4) Just scripts"
echo "5) Just Claude/AI tools"
echo "6) Just code indexing"
echo "7) Pick specific files"
echo ""
read -p "Choice [1]: " choice
choice=${choice:-1}

echo ""

case $choice in
    1)
        echo "Installing full development setup..."
        # Copy all config files
        for file in .pre-commit-config.yaml pyproject.toml .flake8 pytest.ini .gitignore .secrets.baseline; do
            if [[ -f "$TEMP_DIR/templates/config/$file" ]]; then
                cp "$TEMP_DIR/templates/config/$file" .
                echo "  ✓ $file"
            fi
        done
        # Copy directories
        for dir in scripts hooks indexing; do
            if [[ -d "$TEMP_DIR/templates/$dir" ]]; then
                cp -r "$TEMP_DIR/templates/$dir" .
                echo "  ✓ $dir/"
            fi
        done
        # Copy CLAUDE.md
        if [[ -f "$TEMP_DIR/templates/CLAUDE.md" ]]; then
            cp "$TEMP_DIR/templates/CLAUDE.md" .
            echo "  ✓ CLAUDE.md"
        fi
        ;;
    2)
        echo "Installing pre-commit hooks..."
        cp "$TEMP_DIR/templates/config/.pre-commit-config.yaml" .
        echo "  ✓ .pre-commit-config.yaml"
        ;;
    3)
        echo "Installing Python configuration..."
        for file in pyproject.toml .flake8 pytest.ini; do
            if [[ -f "$TEMP_DIR/templates/config/$file" ]]; then
                cp "$TEMP_DIR/templates/config/$file" .
                echo "  ✓ $file"
            fi
        done
        ;;
    4)
        echo "Installing scripts..."
        mkdir -p scripts
        cp -r "$TEMP_DIR/templates/scripts/"* scripts/
        chmod +x scripts/*.sh
        echo "  ✓ scripts/"
        ;;
    5)
        echo "Installing Claude/AI tools..."
        cp -r "$TEMP_DIR/templates/hooks" .
        cp "$TEMP_DIR/templates/CLAUDE.md" .
        echo "  ✓ hooks/"
        echo "  ✓ CLAUDE.md"
        ;;
    6)
        echo "Installing code indexing..."
        cp -r "$TEMP_DIR/templates/indexing" .
        echo "  ✓ indexing/"
        ;;
    7)
        echo "Available files:"
        echo ""
        cd "$TEMP_DIR/templates"
        find . -type f | grep -v "^./.git" | sort
        cd - > /dev/null
        echo ""
        echo "Enter files to copy (space-separated, or 'cancel'):"
        read -r files
        if [[ "$files" != "cancel" ]]; then
            for file in $files; do
                file=${file#./}  # Remove leading ./
                if [[ -f "$TEMP_DIR/templates/$file" ]]; then
                    # Create directory if needed
                    dir=$(dirname "$file")
                    [[ "$dir" != "." ]] && mkdir -p "$dir"
                    cp "$TEMP_DIR/templates/$file" "$file"
                    echo "  ✓ $file"
                else
                    echo "  ✗ $file (not found)"
                fi
            done
        fi
        ;;
esac

echo -e "\n${GREEN}✅ Done!${NC}"
echo ""
echo "Next steps:"

# Suggest next steps based on what was installed
if [[ $choice == 1 ]] || [[ $choice == 4 ]]; then
    echo "• Set up environment: ./scripts/setup-venv.sh"
fi
if [[ $choice == 1 ]] || [[ $choice == 2 ]]; then
    echo "• Install pre-commit: pre-commit install"
fi
if [[ $choice == 1 ]] || [[ $choice == 6 ]]; then
    echo "• Start code indexing: cd indexing && ./start-indexer.sh"
fi
if [[ $choice == 1 ]] || [[ $choice == 5 ]]; then
    echo "• Install Claude hooks: ./hooks/install-claude-hooks.sh"
fi

echo "• Review changes: git diff"
echo "• Commit: git add . && git commit -m 'chore: add dev templates'"
