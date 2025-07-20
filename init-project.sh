#!/bin/bash
# Initialize a new project with Claude development template
set -e

if [[ -z "$1" ]]; then
    echo "Usage: $0 <project-name>"
    exit 1
fi

PROJECT_NAME="$1"
# TEMPLATES_REPO="https://github.com/dhalem/claude_template.git"  # Currently unused

echo "🚀 Creating new project: $PROJECT_NAME"

# Create project directory
mkdir -p "$PROJECT_NAME"
cd "$PROJECT_NAME"

# Initialize git
git init

# Create basic structure
mkdir -p {src,tests,docs}

# Create initial files
cat > src/__init__.py << 'PYEOF'
"""$PROJECT_NAME package."""
__version__ = "0.1.0"
PYEOF

cat > tests/test_example.py << 'PYEOF'
"""Example test file."""
def test_example():
    """Example test."""
    assert True
PYEOF

cat > README.md << MDEOF
# $PROJECT_NAME

## Setup

\`\`\`bash
# Get development templates
curl -O https://raw.githubusercontent.com/dhalem/claude_template/main/pull-templates.sh
chmod +x pull-templates.sh
./pull-templates.sh

# Set up environment
./scripts/setup-venv.sh
source venv/bin/activate
./scripts/setup-pre-commit.sh
\`\`\`

## Development

\`\`\`bash
# Activate environment
source venv/bin/activate

# Run tests
pytest

# Check code quality
pre-commit run --all-files
\`\`\`
MDEOF

# Download and run pull-templates
echo "📥 Getting development templates..."
curl -sO https://raw.githubusercontent.com/dhalem/claude_template/main/pull-templates.sh
chmod +x pull-templates.sh

# Auto-select option 1 (everything)
echo "1" | ./pull-templates.sh

echo "✅ Project initialized: $PROJECT_NAME"
echo ""
echo "Next steps:"
echo "cd $PROJECT_NAME"
echo "./scripts/setup-venv.sh"
echo "source venv/bin/activate"
