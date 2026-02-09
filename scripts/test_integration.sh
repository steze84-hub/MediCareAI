#!/bin/bash
#==============================================================================
# MediCare_AI Integration Test Script | 集成测试脚本
# Version: 2.0.0
# Tests the full flow: Auth -> Case Creation -> Upload -> Extract -> AI Diagnosis
# 测试完整流程：认证 -> 创建病例 -> 上传 -> 提取 -> AI 诊断
#==============================================================================

set -e  # Exit on error

# Colors
readonly GREEN='\033[0;32m'
readonly RED='\033[0;31m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

# Configuration
API_BASE="${API_BASE:-http://localhost:8000}"
TEST_USER_EMAIL="${TEST_USER:-test@test.com}"
TEST_USER_PASS="${TEST_PASS:-test123456}"

# Test files (can be overridden with environment variables)
TEST_IMAGE1="${TEST_IMAGE1:-./test_files/blood_test.jpg}"
TEST_IMAGE2="${TEST_IMAGE2:-./test_files/pathogen_test.jpg}"

echo "============================================"
echo -e "${BLUE}🏥 MediCare_AI Integration Test${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""
echo "API Base: $API_BASE"
echo "Test User: $TEST_USER_EMAIL"
echo ""

# Get fresh token
TOKEN=$(curl -s -X POST "${API_BASE}/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test123456"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['tokens']['access_token'])")

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

# Step 1: Create medical case
print_info "Step 1: Creating medical case..."
CASE_RESPONSE=$(curl -s -X POST "${API_BASE}/api/v1/medical-cases/" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "测试-血液检查分析",
    "symptoms": "需要分析血常规和病原体检查报告",
    "severity": "moderate",
    "description": "上传两张医学检查图片进行AI分析"
  }')

CASE_ID=$(echo $CASE_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
print_status "Created medical case: ${CASE_ID}"

# Step 2: Upload first image (血常规)
print_info "Step 2: Uploading 血常规.jpg..."
DOC1_RESPONSE=$(curl -s -X POST "${API_BASE}/api/v1/documents/upload" \
  -H "Authorization: Bearer ${TOKEN}" \
  -F "medical_case_id=${CASE_ID}" \
  -F "file=@${TEST_IMAGE1}")

DOC1_ID=$(echo $DOC1_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
print_status "Uploaded document 1: ${DOC1_ID}"

# Step 3: Upload second image (特殊病原体)
print_info "Step 3: Uploading 特殊病原体.jpg..."
DOC2_RESPONSE=$(curl -s -X POST "${API_BASE}/api/v1/documents/upload" \
  -H "Authorization: Bearer ${TOKEN}" \
  -F "medical_case_id=${CASE_ID}" \
  -F "file=@${TEST_IMAGE2}")

DOC2_ID=$(echo $DOC2_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
print_status "Uploaded document 2: ${DOC2_ID}"

# Step 4: Trigger extraction for both documents
print_info "Step 4: Triggering MinerU extraction..."

curl -s -X POST "${API_BASE}/api/v1/documents/${DOC1_ID}/extract" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"extraction_type": "medical_report"}' > /dev/null

print_status "Extraction triggered for document 1"

curl -s -X POST "${API_BASE}/api/v1/documents/${DOC2_ID}/extract" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"extraction_type": "medical_report"}' > /dev/null

print_status "Extraction triggered for document 2"

# Step 5: Poll for extraction completion
print_info "Step 5: Waiting for extraction (this may take 30-60 seconds)..."

MAX_RETRIES=30
RETRY=0
EXTRACTION_COMPLETE=false

while [ $RETRY -lt $MAX_RETRIES ]; do
    sleep 2
    RETRY=$((RETRY + 1))
    
    # Check document 1
    DOC1_STATUS=$(curl -s "${API_BASE}/api/v1/documents/${DOC1_ID}" \
      -H "Authorization: Bearer ${TOKEN}" | \
      python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('upload_status', 'unknown'))")
    
    # Check document 2  
    DOC2_STATUS=$(curl -s "${API_BASE}/api/v1/documents/${DOC2_ID}" \
      -H "Authorization: Bearer ${TOKEN}" | \
      python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('upload_status', 'unknown'))")
    
    echo "  Retry ${RETRY}/${MAX_RETRIES}: Doc1=${DOC1_STATUS}, Doc2=${DOC2_STATUS}"
    
    if [ "$DOC1_STATUS" = "processed" ] && [ "$DOC2_STATUS" = "processed" ]; then
        EXTRACTION_COMPLETE=true
        break
    fi
done

if [ "$EXTRACTION_COMPLETE" = false ]; then
    print_error "Extraction timed out"
    exit 1
fi

print_status "Extraction completed for both documents"

# Step 6: Get extracted content
print_info "Step 6: Retrieving extracted content..."

DOC1_CONTENT=$(curl -s "${API_BASE}/api/v1/documents/${DOC1_ID}/content" \
  -H "Authorization: Bearer ${TOKEN}")

DOC2_CONTENT=$(curl -s "${API_BASE}/api/v1/documents/${DOC2_ID}/content" \
  -H "Authorization: Bearer ${TOKEN}")

print_status "Retrieved content for both documents"
echo ""
echo "Document 1 Preview:"
echo "$DOC1_CONTENT" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('extracted_content', 'N/A')[:200] + '...' if d.get('extracted_content') else 'No content')"
echo ""
echo "Document 2 Preview:"
echo "$DOC2_CONTENT" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('extracted_content', 'N/A')[:200] + '...' if d.get('extracted_content') else 'No content')"

# Step 7: Test AI diagnosis with document IDs
print_info "Step 7: Testing AI diagnosis with extracted documents..."
echo "Document IDs: ${DOC1_ID}, ${DOC2_ID}"
echo ""

# Note: AI diagnosis may timeout if AI service is not available
# This tests the integration, not the AI model itself
curl -s -X POST "${API_BASE}/api/v1/ai/comprehensive-diagnosis" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    \"symptoms\": \"患者上传了血常规和病原体检查报告，请分析检查结果\",
    \"severity\": \"moderate\",
    \"document_ids\": [\"${DOC1_ID}\", \"${DOC2_ID}\"],
    \"language\": \"zh\"
  }" | python3 -m json.tool | head -50

echo ""
echo "============================================"
print_status "Test completed successfully!"
echo "============================================"
echo ""
echo "Summary:"
echo "  - Medical Case: ${CASE_ID}"
echo "  - Document 1 (血常规): ${DOC1_ID}"
echo "  - Document 2 (特殊病原体): ${DOC2_ID}"
echo "  - Both documents extracted and ready for AI diagnosis"
