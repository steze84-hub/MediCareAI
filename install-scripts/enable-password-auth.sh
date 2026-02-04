#!/bin/bash
# Run this on the Ubuntu VM (192.168.50.195) to enable password authentication

echo "Enabling password authentication for SSH..."

# Backup original config
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup.$(date +%Y%m%d)

# Enable password authentication
sudo sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config
sudo sed -i 's/^#*ChallengeResponseAuthentication.*/ChallengeResponseAuthentication yes/' /etc/ssh/sshd_config

# Restart SSH service
sudo systemctl restart sshd

echo "Password authentication enabled!"
echo "You can now connect with: ssh houge@192.168.50.195"
echo ""
echo "After testing, you can restore the original config with:"
echo "sudo cp /etc/ssh/sshd_config.backup.* /etc/ssh/sshd_config"
echo "sudo systemctl restart sshd"
