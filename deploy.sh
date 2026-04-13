#!/bin/bash
# 배포 자동화 스크립트 (Linux/Mac)
# 사용: bash deploy.sh

set -e  # 오류 발생 시 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 로그 함수
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 현재 디렉토리 확인
if [ ! -f "requirements.txt" ]; then
    log_error "requirements.txt를 찾을 수 없습니다. 프로젝트 루트 디렉토리에서 실행하세요."
    exit 1
fi

log_info "배포 스크립트 시작..."

# 1. 환경 설정 확인
log_info "1️⃣  환경 설정 확인..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        log_warn ".env 파일이 없습니다. .env.example을 복사합니다."
        cp .env.example .env
        log_warn "⚠️  .env 파일을 실제 값으로 수정하세요!"
    else
        log_error ".env 또는 .env.example 파일이 없습니다."
        exit 1
    fi
else
    log_info ".env 파일 확인됨"
fi

# 2. 가상환경 생성/활성화
log_info "2️⃣  Python 가상환경 확인..."
if [ ! -d "venv" ]; then
    log_info "가상환경 생성 중..."
    python3 -m venv venv
else
    log_info "기존 가상환경 사용"
fi

source venv/bin/activate
log_info "가상환경 활성화됨"

# 3. Python 버전 확인
log_info "3️⃣  Python 버전 확인..."
PYTHON_VERSION=$(python --version | awk '{print $2}')
log_info "Python 버전: $PYTHON_VERSION"

# 4. 의존성 설치
log_info "4️⃣  의존성 설치 중..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
log_info "의존성 설치 완료"

# 5. 테스트 실행
log_info "5️⃣  테스트 실행 중..."
if command -v pytest &> /dev/null; then
    pytest tests/ -q --tb=short || log_warn "일부 테스트가 실패했습니다."
else
    log_warn "pytest가 설치되지 않았습니다. 테스트 건너뜀."
fi

# 6. Node.js/npm 확인
log_info "6️⃣  Node.js 환경 확인..."
if command -v npm &> /dev/null; then
    log_info "npm 버전: $(npm --version)"
    log_info "frontend 의존성 설치 중..."
    cd frontend
    npm install -q
    cd ..
    log_info "frontend 의존성 설치 완료"
else
    log_warn "npm이 설치되지 않았습니다. 프론트엔드를 수동으로 구성하세요."
fi

# 7. 디렉토리 생성
log_info "7️⃣  필요한 디렉토리 생성..."
mkdir -p logs
mkdir -p data
mkdir -p data/cache
log_info "디렉토리 생성 완료"

# 8. 권한 설정
log_info "8️⃣  파일 권한 설정..."
chmod 600 .env
chmod -R 755 logs
log_info "권한 설정 완료"

# 9. 요약 정보 출력
log_info "9️⃣  배포 준비 완료!"
echo ""
echo "📋 배포 정보:"
echo "═══════════════════════════════════════"
echo "프로젝트: 사내 NAS 검색 MCP"
echo "Python: $PYTHON_VERSION"
echo "Node.js: $(node --version 2>/dev/null || echo '설치 필요')"
echo "npm: $(npm --version 2>/dev/null || echo '설치 필요')"
echo ""
echo "🚀 서버 시작 방법:"
echo "═══════════════════════════════════════"
echo "1. Flask 백엔드:"
echo "   source venv/bin/activate"
echo "   python app.py"
echo ""
echo "2. Vite 프론트엔드 (새 터미널):"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "3. 크롤러 (선택사항, 새 터미널):"
echo "   source venv/bin/activate"
echo "   python -m src.crawler"
echo ""
echo "✅ 배포 완료!"
echo "═══════════════════════════════════════"
