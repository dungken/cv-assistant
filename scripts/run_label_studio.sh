#!/bin/bash
# scripts/run_label_studio.sh

set -e

echo "🎨 Starting Label Studio..."

if [ -d "label_studio_env" ]; then
    echo "📦 Activating Label Studio environment..."
    source label_studio_env/bin/activate
    
    echo "🚀 Launching Label Studio server..."
    echo "Access it at: http://localhost:8080"
    echo "(Press Ctrl+C in this terminal if you want to stop it, but it's better to run in a separate tab if you need the manager)"
    
    # Run label-studio. It will block until Ctrl+C
    label-studio start
else
    echo "❌ Error: label_studio_env not found."
    echo "Please ensure Label Studio is installed in 'label_studio_env'."
    exit 1
fi
