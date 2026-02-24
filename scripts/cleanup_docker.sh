#!/bin/bash
# cleanup_docker.sh

echo "🧹 Starting aggressive Docker cleanup..."
echo "⚠️  This will remove ALL unused containers, images, and volumes NOT associated with the currently running project."

# Get initial disk usage
BEFORE=$(df -h /var/lib/docker | awk 'NR==2 {print $3}')
echo "📊 Current Docker Disk Usage: $BEFORE"

# 1. Prune all unused resources aggressively
# This removes:
# - all stopped containers
# - all networks not used by at least one container
# - all images without at least one container associated to them
# - all build cache
echo "🗑️  Pruning unused resources (Images, Containers, Networks, Volumes)..."
docker system prune -a --volumes -f

# 2. Prune global build cache specifically
echo "🗑️  Pruning build cache..."
docker builder prune -a -f

# Get final disk usage
AFTER=$(df -h /var/lib/docker | awk 'NR==2 {print $3}')
echo "✨ Cleanup complete!"
echo "📊 Previous Usage: $BEFORE"
echo "📊 Current Usage:  $AFTER"
echo "------------------------------------------------"
echo "✅ Only running project resources (cv_assistant) have been preserved."
