# MediCare_AI Ubuntu 24.04 LTS Installation Guide

## Overview

This guide documents the complete installation process for MediCare_AI on Ubuntu 24.04 LTS, which will serve as the foundation for creating a universal one-click installation script supporting multiple Linux distributions.

## System Requirements

### Minimum Requirements
- **OS**: Ubuntu 24.04 LTS (Noble Numbat)
- **CPU**: 2 cores
- **RAM**: 4 GB
- **Storage**: 20 GB free space
- **Network**: Internet connection for downloading Docker images

### Recommended Requirements
- **CPU**: 4+ cores
- **RAM**: 8+ GB
- **Storage**: 50+ GB SSD

## Installation Steps

### Step 1: System Preparation

```bash
# Check Ubuntu version
cat /etc/os-release
# Expected: Ubuntu 24.04 LTS

# Update system packages
sudo apt-get update
sudo apt-get upgrade -y
```

### Step 2: Install Dependencies

```bash
# Install required packages
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    software-properties-common \
    git \
    wget \
    vim \
    htop \
    net-tools
```

### Step 3: Install Docker

Ubuntu 24.04 uses Docker's official repository for the latest version:

```bash
# Remove old Docker versions if exist
sudo apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

# Add Docker's official GPG key
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add Docker repository
echo \
    "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
    "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
    sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update and install Docker
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add user to docker group (requires logout/login)
sudo usermod -aG docker $USER

# Enable and start Docker service
sudo systemctl enable docker
sudo systemctl start docker
```

**Note**: After adding user to docker group, you need to log out and log back in for changes to take effect.

### Step 4: Verify Docker Installation

```bash
# Check Docker version
docker --version
# Expected: Docker version 24.x.x or higher

# Check Docker Compose version
docker compose version
# Expected: Docker Compose version v2.x.x

# Test Docker (optional)
docker run hello-world
```

### Step 5: Create Project Directory

```bash
# Create project directory
sudo mkdir -p /opt/medicare-ai
sudo chown $USER:$USER /opt/medicare-ai

# Navigate to project directory
cd /opt/medicare-ai
```

### Step 6: Configure Environment

Create the `.env` file with appropriate settings:

```bash
cat > /opt/medicare-ai/.env << 'EOF'
# Database Configuration
POSTGRES_PASSWORD=medicare123456

# Redis Configuration
REDIS_PASSWORD=redis123456

# JWT Configuration
JWT_SECRET_KEY=MedicareAI-Secret-Key-For-JWT-Authentication-2024
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# MinerU API Configuration
MINERU_TOKEN=your_mineru_token_here

# AI API Configuration (Update this for your environment)
AI_API_KEY=zhanxiaopi
AI_API_URL=http://192.168.50.253:8033/v1/
AI_MODEL_ID=unsloth/Nemotron-3-Nano-30B-A3B-GGUF:BF16

# File Upload Configuration
MAX_FILE_SIZE=200000000
UPLOAD_PATH=/app/uploads

# Security Configuration
CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]
ALLOWED_HOSTS=["localhost", "127.0.0.1"]

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json

# Development Configuration
DEBUG=false
TESTING=false
EOF
```

**Important**: Update `AI_API_URL` to match your AI server address.

### Step 7: Extract Project Files

Copy the MediCare_AI project files to the installation directory:

```bash
# If you have a tar.gz archive
tar -xzf MediCare_AI-v1.0.2.tar.gz -C /opt/medicare-ai --strip-components=1

# Or clone from repository (if available)
# git clone <repository-url> /opt/medicare-ai
```

### Step 8: Configure Firewall

```bash
# Allow required ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8000/tcp  # API (optional, for direct access)
sudo ufw allow 3000/tcp  # Frontend (optional, for direct access)

# Enable firewall if not already enabled
sudo ufw --force enable

# Check firewall status
sudo ufw status
```

### Step 9: Build and Start Services

```bash
cd /opt/medicare-ai

# Build and start all services
docker compose up -d --build

# Wait for services to start
sleep 10
```

### Step 10: Initialize Database

```bash
cd /opt/medicare-ai

# Initialize database tables
docker compose exec -T backend python -c "
import asyncio
import sys
sys.path.append('/app')
from app.db.init_db import init_db
asyncio.run(init_db())
print('Database initialized successfully!')
"
```

### Step 11: Verify Installation

```bash
# Check all services are running
docker compose ps

# Expected output:
# NAME                STATUS
# medicare_backend    Up
# medicare_frontend   Up
# medicare_nginx      Up
# medicare_postgres   Up (healthy)
# medicare_redis      Up

# Test health endpoint
curl http://localhost:8000/health

# Expected output:
# {"status":"healthy","python_version":"3.12.x",...}
```

### Step 12: Test Application

1. **Access the frontend**: Open browser to `http://localhost` or `http://<server-ip>`
2. **Test user registration**: Create a test account
3. **Test symptom submission**: Submit symptoms and verify AI diagnosis
4. **Check medical records**: View generated records

## Post-Installation Configuration

### Create Systemd Service

Create a systemd service for automatic startup:

```bash
sudo tee /etc/systemd/system/medicare-ai.service > /dev/null << 'EOF'
[Unit]
Description=MediCare_AI Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/medicare-ai
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

# Enable service
sudo systemctl daemon-reload
sudo systemctl enable medicare-ai.service
```

### Management Commands

```bash
# Start application
cd /opt/medicare-ai && docker compose up -d

# Stop application
cd /opt/medicare-ai && docker compose down

# View logs
cd /opt/medicare-ai && docker compose logs -f

# View backend logs only
cd /opt/medicare-ai && docker compose logs -f backend

# Restart specific service
cd /opt/medicare-ai && docker compose restart backend

# Update application (pull latest images and restart)
cd /opt/medicare-ai && docker compose pull && docker compose up -d
```

## Troubleshooting

### Issue 1: Permission Denied when running Docker commands

**Solution**: Log out and log back in, or run:
```bash
newgrp docker
```

### Issue 2: Port already in use

**Solution**: Check what's using the port:
```bash
sudo lsof -i :80
sudo lsof -i :8000
```

Stop the conflicting service or modify ports in `docker-compose.yml`.

### Issue 3: AI diagnosis not working

**Solution**: 
1. Verify AI server is accessible:
   ```bash
   curl http://<ai-server-ip>:8033/v1/models
   ```
2. Check AI_API_URL in `.env` file
3. Check backend logs:
   ```bash
   docker compose logs backend | grep -i error
   ```

### Issue 4: Database connection failed

**Solution**:
1. Check PostgreSQL container status
2. Verify DATABASE_URL in environment
3. Check logs:
   ```bash
   docker compose logs postgres
   ```

## Security Considerations

1. **Change default passwords**: Update all default passwords in `.env` file
2. **Use HTTPS**: For production, configure SSL certificates
3. **Firewall**: Only open necessary ports
4. **Regular updates**: Keep system and Docker images updated

## Files Structure

After installation, the directory structure should be:

```
/opt/medicare-ai/
├── .env                      # Environment configuration
├── docker-compose.yml        # Docker Compose configuration
├── backend/                  # Backend application
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
├── frontend/                 # Frontend application
│   ├── Dockerfile
│   └── *.html
├── docker/
│   └── nginx/
│       ├── Dockerfile
│       └── nginx.conf
└── docs/                     # Documentation
```

## Version Information

- **OS**: Ubuntu 24.04 LTS
- **Docker**: 24.x.x or higher
- **Docker Compose**: v2.x.x
- **Python**: 3.12.x (inside container)
- **PostgreSQL**: 17
- **Redis**: 7.4

## Next Steps

1. Configure backup for database and uploads
2. Set up monitoring and alerting
3. Configure SSL/HTTPS for production
4. Test all features thoroughly
5. Document any custom configurations

## References

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Ubuntu Server Guide](https://ubuntu.com/server/docs)
- [MediCare_AI Project Documentation](README.md)

---

**Document Version**: 1.0  
**Last Updated**: 2025-02-02  
**Compatible With**: MediCare_AI v1.0.2+
