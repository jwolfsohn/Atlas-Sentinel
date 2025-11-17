#!/bin/bash
# Initialize environment file from example

cd "$(dirname "$0")"

if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ Created .env file from .env.example"
        echo "📝 Please review .env and update any settings as needed"
    else
        echo "⚠️  .env.example not found, creating basic .env file"
        cat > .env << EOF
# Atlas Sentinel Environment Configuration
DATA_DIR=.data
API_HOST=0.0.0.0
API_PORT=8000
EOF
        echo "✅ Created basic .env file"
    fi
else
    echo "ℹ️  .env file already exists, skipping"
fi

