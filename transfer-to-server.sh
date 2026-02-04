#!/bin/bash
#
# Transfer MediCare_AI v1.0.2 to target server
# Usage: ./transfer-to-server.sh <target-server-ip>
#

set -e

TARGET_IP="${1:-10.86.7.197}"
TARGET_USER="houge"
TARGET_DIR="/home/houge"
PACKAGE="MediCare_AI-v1.0.2.tar.gz"
CHECKSUM="MediCare_AI-v1.0.2.tar.gz.sha256"
RELEASE_NOTES="RELEASE-v1.0.2.txt"

echo "==================================="
echo "MediCare_AI v1.0.2 Transfer Script"
echo "==================================="
echo ""
echo "Target: $TARGET_USER@$TARGET_IP"
echo "Package: $PACKAGE"
echo ""

# Verify files exist
echo "[1/5] Verifying local files..."
if [ ! -f "$PACKAGE" ]; then
    echo "ERROR: $PACKAGE not found!"
    exit 1
fi

if [ ! -f "$CHECKSUM" ]; then
    echo "ERROR: $CHECKSUM not found!"
    exit 1
fi

if [ ! -f "$RELEASE_NOTES" ]; then
    echo "WARNING: $RELEASE_NOTES not found"
fi

echo "✓ Local files verified"
echo ""

# Verify checksum
echo "[2/5] Verifying package integrity..."
sha256sum -c "$CHECKSUM"
echo "✓ Package integrity verified"
echo ""

# Test SSH connection
echo "[3/5] Testing SSH connection..."
if ! ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no "$TARGET_USER@$TARGET_IP" "echo 'SSH OK'" 2>/dev/null; then
    echo "ERROR: Cannot connect to $TARGET_IP"
    echo "Make sure:"
    echo "  1. SSH key is set up: ssh-copy-id $TARGET_USER@$TARGET_IP"
    echo "  2. Target server is online"
    echo "  3. SSH service is running on target"
    exit 1
fi
echo "✓ SSH connection successful"
echo ""

# Create remote directory
echo "[4/5] Preparing remote directory..."
ssh "$TARGET_USER@$TARGET_IP" "mkdir -p $TARGET_DIR/MediCare_AI-v1.0.2 && ls -la $TARGET_DIR/MediCare_AI-v1.0.2" 2>/dev/null || {
    echo "Creating directory..."
    ssh "$TARGET_USER@$TARGET_IP" "mkdir -p $TARGET_DIR/MediCare_AI-v1.0.2"
}
echo "✓ Remote directory ready"
echo ""

# Transfer files
echo "[5/5] Transferring files..."
echo "  - Uploading $PACKAGE..."
scp -o StrictHostKeyChecking=no "$PACKAGE" "$TARGET_USER@$TARGET_IP:$TARGET_DIR/MediCare_AI-v1.0.2/"

echo "  - Uploading $CHECKSUM..."
scp -o StrictHostKeyChecking=no "$CHECKSUM" "$TARGET_USER@$TARGET_IP:$TARGET_DIR/MediCare_AI-v1.0.2/"

if [ -f "$RELEASE_NOTES" ]; then
    echo "  - Uploading $RELEASE_NOTES..."
    scp -o StrictHostKeyChecking=no "$RELEASE_NOTES" "$TARGET_USER@$TARGET_IP:$TARGET_DIR/MediCare_AI-v1.0.2/"
fi

echo "✓ Transfer complete"
echo ""

# Verify remote files
echo "Verifying remote files..."
ssh "$TARGET_USER@$TARGET_IP" "cd $TARGET_DIR/MediCare_AI-v1.0.2 && sha256sum -c $CHECKSUM"
echo "✓ Remote verification successful"
echo ""

echo "==================================="
echo "Transfer Complete!"
echo "==================================="
echo ""
echo "Files transferred to: $TARGET_USER@$TARGET_IP:$TARGET_DIR/MediCare_AI-v1.0.2/"
echo ""
echo "Next steps on target server:"
echo "  1. SSH to server: ssh $TARGET_USER@$TARGET_IP"
echo "  2. Navigate to directory: cd $TARGET_DIR/MediCare_AI-v1.0.2"
echo "  3. Extract package: tar -xzf $PACKAGE"
echo "  4. Install: sudo bash install-scripts/install-ubuntu-2404.sh"
echo ""
echo "Or run installation directly:"
echo "  ssh $TARGET_USER@$TARGET_IP 'cd $TARGET_DIR/MediCare_AI-v1.0.2 && tar -xzf $PACKAGE && sudo bash install-scripts/install-ubuntu-2404.sh'"
echo ""
