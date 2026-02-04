#!/bin/bash
# Generate SSH key pair without passphrase for automated testing

KEY_NAME="medicare_ai_test_key"
KEY_PATH="$HOME/.ssh/${KEY_NAME}"

echo "Generating SSH key pair without passphrase..."
ssh-keygen -t ed25519 -C "medicare-ai-test" -f "$KEY_PATH" -N ""

echo ""
echo "=== PUBLIC KEY (copy this to VM's authorized_keys) ==="
cat "${KEY_PATH}.pub"
echo ""
echo "=== INSTRUCTIONS ==="
echo "1. Copy the public key above"
echo "2. On the VM (192.168.50.195), run:"
echo "   mkdir -p ~/.ssh"
echo "   echo 'PASTE_PUBLIC_KEY_HERE' >> ~/.ssh/authorized_keys"
echo "   chmod 700 ~/.ssh"
echo "   chmod 600 ~/.ssh/authorized_keys"
echo ""
echo "3. Then you can connect with:"
echo "   ssh -i $KEY_PATH houge@192.168.50.195"
echo ""
echo "Private key saved to: $KEY_PATH"
