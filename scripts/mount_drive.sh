#!/bin/bash

# Configuration
REMOTE_NAME="my-drive" # Changed to match user configuration
REMOTE_PATH="cv_assistant_data" # Folder on your Drive
MOUNT_POINT="/mnt/cv_assistant_data"

echo "☁️ Setting up Cloud Storage (Google Drive)..."

# 1. Check if rclone is installed
if ! command -v rclone &> /dev/null; then
    echo "❌ rclone is not installed. Please install it: sudo apt install rclone"
    exit 1
fi

# 2. Check if remote exists
if ! rclone listremotes | grep -q "^${REMOTE_NAME}:"; then
    echo "❌ Rclone remote '${REMOTE_NAME}' not found."
    echo "Please run 'rclone config' to create a remote named '${REMOTE_NAME}' first."
    exit 1
fi

# 3. Ensure remote folder exists
echo "📁 Ensuring remote folder exists: $REMOTE_NAME:$REMOTE_PATH"
rclone mkdir "$REMOTE_NAME:$REMOTE_PATH"

# 4. Create local mount point
if [ ! -d "$MOUNT_POINT" ]; then
    echo "📁 Creating local mount point: $MOUNT_POINT"
    sudo mkdir -p "$MOUNT_POINT"
    sudo chown $(whoami):$(whoami) "$MOUNT_POINT"
fi

# 5. Mount the drive
echo "🚀 Mounting $REMOTE_NAME:$REMOTE_PATH to $MOUNT_POINT..."
echo "Note: This process will run in the background."

# Using --vfs-cache-mode full for better compatibility with DBs
rclone mount "$REMOTE_NAME:$REMOTE_PATH" "$MOUNT_POINT" \
    --vfs-cache-mode full \
    --daemon

echo "✅ Drive mounted! You can now use $MOUNT_POINT for your data."
echo "------------------------------------------------"
echo "To unmount: fusermount -u $MOUNT_POINT"
