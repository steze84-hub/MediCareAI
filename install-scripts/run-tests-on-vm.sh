#!/bin/bash
#
# MediCare_AI Ubuntu 24.04 LTS - Automated Test Script
# Run this script on the Ubuntu VM (192.168.50.195) to test installation
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Configuration
PROJECT_DIR="/opt/medicare-ai"
AI_API_URL="http://192.168.50.253:8033/v1/"
TEST_RESULTS_FILE="/tmp/medicare-ai-test-results.txt"

# Initialize test results
echo "MediCare_AI Test Results - $(date)" > $TEST_RESULTS_FILE
echo "================================" >> $TEST_RESULTS_FILE

log_info "Starting MediCare_AI automated test on Ubuntu 24.04..."
echo ""

# ============================================
# TEST 1: System Check
# ============================================
log_info "TEST 1: Checking system..."
echo -n "  - OS Version: " >> $TEST_RESULTS_FILE
if grep -q "Ubuntu 24.04" /etc/os-release; then
    log_success "Ubuntu 24.04 LTS detected"
    echo "PASS (Ubuntu 24.04)" >> $TEST_RESULTS_FILE
else
    log_warning "Not Ubuntu 24.04, but continuing..."
    echo "WARNING (Not Ubuntu 24.04)" >> $TEST_RESULTS_FILE
fi

echo -n "  - Architecture: " >> $TEST_RESULTS_FILE
ARCH=$(dpkg --print-architecture)
log_info "Architecture: $ARCH"
echo "$ARCH" >> $TEST_RESULTS_FILE

echo -n "  - Memory: " >> $TEST_RESULTS_FILE
MEM=$(free -h | grep Mem | awk '{print $2}')
log_info "Memory: $MEM"
echo "$MEM" >> $TEST_RESULTS_FILE

echo -n "  - Disk Space: " >> $TEST_RESULTS_FILE
DISK=$(df -h / | tail -1 | awk '{print $4}')
log_info "Available disk: $DISK"
echo "$DISK" >> $TEST_RESULTS_FILE

# ============================================
# TEST 2: Docker Installation
# ============================================
echo ""
log_info "TEST 2: Installing Docker..."
echo -n "  - Docker Installation: " >> $TEST_RESULTS_FILE

if ! command -v docker &> /dev/null; then
    log_info "Docker not found, installing..."
    
    # Remove old versions
    sudo apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
    
    # Install dependencies
    sudo apt-get update
    sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
    
    # Add Docker GPG key
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg
    
    # Add repository
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
        sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    # Add user to docker group
    sudo usermod -aG docker $USER
    
    log_success "Docker installed"
    echo "INSTALLED" >> $TEST_RESULTS_FILE
else
    log_success "Docker already installed"
    echo "ALREADY_INSTALLED" >> $TEST_RESULTS_FILE
fi

echo -n "  - Docker Version: " >> $TEST_RESULTS_FILE
DOCKER_VERSION=$(docker --version)
log_info "$DOCKER_VERSION"
echo "$DOCKER_VERSION" >> $TEST_RESULTS_FILE

echo -n "  - Docker Compose: " >> $TEST_RESULTS_FILE
COMPOSE_VERSION=$(docker compose version)
log_info "$COMPOSE_VERSION"
echo "$COMPOSE_VERSION" >> $TEST_RESULTS_FILE

# ============================================
# TEST 3: Project Setup
# ============================================
echo ""
log_info "TEST 3: Setting up project..."
echo -n "  - Project Directory: " >> $TEST_RESULTS_FILE

sudo mkdir -p $PROJECT_DIR
sudo chown $USER:$USER $PROJECT_DIR
log_success "Project directory created: $PROJECT_DIR"
echo "CREATED ($PROJECT_DIR)" >> $TEST_RESULTS_FILE

# ============================================
# TEST 4: Environment Configuration
# ============================================
echo ""
log_info "TEST 4: Configuring environment..."
echo -n "  - Environment File: " >> $TEST_RESULTS_FILE

cat > $PROJECT_DIR/.env << EOF
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

# AI API Configuration
AI_API_KEY=zhanxiaopi
AI_API_URL=$AI_API_URL
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

log_success "Environment file created"
echo "CREATED" >> $TEST_RESULTS_FILE

# ============================================
# TEST 5: Check Project Files
# ============================================
echo ""
log_info "TEST 5: Checking project files..."
echo -n "  - Project Files: " >> $TEST_RESULTS_FILE

if [ -f "$PROJECT_DIR/docker-compose.yml" ]; then
    log_success "docker-compose.yml found"
    echo "PRESENT" >> $TEST_RESULTS_FILE
else
    log_error "Project files not found!"
    log_info "Please copy project files to $PROJECT_DIR"
    echo "MISSING (Please copy files)" >> $TEST_RESULTS_FILE
    exit 1
fi

# ============================================
# TEST 6: Build and Start Services
# ============================================
echo ""
log_info "TEST 6: Building and starting services..."
echo -n "  - Docker Build: " >> $TEST_RESULTS_FILE

cd $PROJECT_DIR
if docker compose build --no-cache backend 2>&1 | tee /tmp/docker-build.log | tail -20; then
    log_success "Docker build completed"
    echo "SUCCESS" >> $TEST_RESULTS_FILE
else
    log_error "Docker build failed"
    echo "FAILED" >> $TEST_RESULTS_FILE
    exit 1
fi

echo -n "  - Starting Services: " >> $TEST_RESULTS_FILE
if docker compose up -d 2>&1 | tee /tmp/docker-up.log; then
    log_success "Services started"
    echo "SUCCESS" >> $TEST_RESULTS_FILE
else
    log_error "Failed to start services"
    echo "FAILED" >> $TEST_RESULTS_FILE
    exit 1
fi

# Wait for services to be ready
log_info "Waiting for services to be ready (30s)..."
sleep 30

# ============================================
# TEST 7: Initialize Database
# ============================================
echo ""
log_info "TEST 7: Initializing database..."
echo -n "  - Database Init: " >> $TEST_RESULTS_FILE

if docker compose exec -T backend python -c "
import asyncio
import sys
sys.path.append('/app')
from app.db.init_db import init_db
asyncio.run(init_db())
print('Database initialized successfully!')
" 2>&1 | tee /tmp/db-init.log; then
    log_success "Database initialized"
    echo "SUCCESS" >> $TEST_RESULTS_FILE
else
    log_error "Database initialization failed"
    echo "FAILED" >> $TEST_RESULTS_FILE
fi

# ============================================
# TEST 8: Health Check
# ============================================
echo ""
log_info "TEST 8: Health check..."
echo -n "  - Health Endpoint: " >> $TEST_RESULTS_FILE

HEALTH_RESPONSE=$(curl -s http://localhost:8000/health 2>&1)
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    log_success "Health check passed"
    echo "PASS" >> $TEST_RESULTS_FILE
    
    echo -n "  - Python Version: " >> $TEST_RESULTS_FILE
    PYTHON_VER=$(echo "$HEALTH_RESPONSE" | grep -o '"python_version":"[^"]*"' | cut -d'"' -f4)
    log_info "Python: $PYTHON_VER"
    echo "$PYTHON_VER" >> $TEST_RESULTS_FILE
else
    log_error "Health check failed"
    echo "FAIL" >> $TEST_RESULTS_FILE
fi

# ============================================
# TEST 9: User Registration Test
# ============================================
echo ""
log_info "TEST 9: Testing user registration..."
echo -n "  - User Registration: " >> $TEST_RESULTS_FILE

REGISTER_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/register \
    -H "Content-Type: application/json" \
    -d '{
        "email": "test@medicare.ai",
        "password": "testpassword123",
        "full_name": "Test User"
    }' 2>&1)

if echo "$REGISTER_RESPONSE" | grep -q "test@medicare.ai"; then
    log_success "User registration successful"
    echo "PASS" >> $TEST_RESULTS_FILE
else
    log_error "User registration failed"
    echo "FAIL" >> $TEST_RESULTS_FILE
fi

# ============================================
# TEST 10: AI Diagnosis Test
# ============================================
echo ""
log_info "TEST 10: Testing AI diagnosis..."
echo -n "  - AI Diagnosis: " >> $TEST_RESULTS_FILE

# Get token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{
        "email": "test@medicare.ai",
        "password": "testpassword123"
    }' | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -n "$TOKEN" ]; then
    log_success "Login successful, got token"
    
    # Test streaming diagnosis
    log_info "Testing streaming diagnosis (may take 30-60s)..."
    timeout 60 curl -N -X POST http://localhost:8000/api/v1/ai/comprehensive-diagnosis-stream \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "symptoms": "咳嗽一周，晚上加重",
            "severity": "中度",
            "disease_category": "respiratory"
        }' 2>&1 | head -20 | tee /tmp/ai-test.log
    
    if grep -q "chunk" /tmp/ai-test.log; then
        log_success "AI diagnosis streaming works"
        echo "PASS" >> $TEST_RESULTS_FILE
    else
        log_warning "AI diagnosis may have issues (check logs)"
        echo "WARNING (check /tmp/ai-test.log)" >> $TEST_RESULTS_FILE
    fi
else
    log_error "Failed to get token"
    echo "FAIL" >> $TEST_RESULTS_FILE
fi

# ============================================
# TEST 11: Service Status
# ============================================
echo ""
log_info "TEST 11: Checking service status..."
docker compose ps >> $TEST_RESULTS_FILE

# ============================================
# Test Complete
# ============================================
echo ""
echo "=============================================="
echo "  Test Complete!"
echo "=============================================="
echo ""
echo "Results saved to: $TEST_RESULTS_FILE"
echo ""
echo "Access Points:"
echo "  - Frontend: http://$(hostname -I | awk '{print $1}')"
echo "  - API: http://$(hostname -I | awk '{print $1}'):8000"
echo "  - API Docs: http://$(hostname -I | awk '{print $1}'):8000/docs"
echo ""
echo "Management Commands:"
echo "  cd $PROJECT_DIR && docker compose logs -f"
echo "  cd $PROJECT_DIR && docker compose ps"
echo "  cd $PROJECT_DIR && docker compose down"
echo ""

# Show summary
cat $TEST_RESULTS_FILE
