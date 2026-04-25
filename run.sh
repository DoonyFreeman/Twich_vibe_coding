#!/bin/bash
# Quick install and run script for Vibe Coding

set -e

echo "Installing Vibe Coding..."

# Install the package
pip install -e .

# Initialize if needed
if [ ! -f .env ]; then
    echo "Creating config files..."
    python -c "from vibe_coding.cli.main import app; app(['init'])"
fi

# Check if configured
source .env 2>/dev/null || true

if [ "$TWITCH_OAUTH_TOKEN" = "oauth:your_token_here" ] || [ -z "$TWITCH_OAUTH_TOKEN" ]; then
    echo ""
    echo "Setup required!"
    echo "1. Edit .env with your Twitch OAuth token"
    echo "2. Edit config.yaml with your channel"
    echo ""
    echo "Then run: vibe run"
else
    echo "Starting bot..."
    vibe run
fi