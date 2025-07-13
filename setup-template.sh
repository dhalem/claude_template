#!/bin/bash
set -e

echo "🚀 Setting up Python Development Template"

# Check Python version
python3 --version >/dev/null 2>&1 || {
    echo "❌ Python 3 is required but not installed."
    exit 1
}

# Run setup scripts
echo "📦 Setting up virtual environment..."
./scripts/setup-venv.sh

echo "🔧 Activating virtual environment..."
source venv/bin/activate

echo "🔨 Setting up pre-commit hooks..."
./scripts/setup-pre-commit.sh

echo "🔍 Setting up code indexing..."
cd indexing && ./setup_code_indexing.sh && cd ..

# Create local configuration
if [[ ! -f "CLAUDE.local.md" ]]; then
    echo "📝 Creating local configuration..."
    cp CLAUDE.local.md.template CLAUDE.local.md
fi

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Install Claude hooks: ./hooks/install-claude-hooks.sh"
echo "3. Start code indexer: cd indexing && ./start-indexer.sh"
echo "4. Customize CLAUDE.local.md for your project"
echo "5. Begin development!"
