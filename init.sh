#!/bin/bash
# Quick init script for Vibe Coding

echo "Initializing Vibe Coding..."

# Install dependencies
pip install -q aiosqlite pyyaml typer python-dotenv rich

# Create config files
python -c "from vibe_coding.cli.main import app; app(['init'])" 2>/dev/null || true

echo ""
echo "Done! Next steps:"
echo "1. Edit .env with your Twitch credentials"
echo "2. Edit config.yaml with your channel"
echo "3. Run: vibe run"