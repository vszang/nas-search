#!/bin/bash
# Docker 배포 스크립트

set -e

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
PROJECT_NAME="${PROJECT_NAME:-intranet-nas-search}"
ENVIRONMENT="${ENVIRONMENT:-development}"

log_info() {
    echo "ℹ️  [INFO] $1"
}

log_success() {
    echo "✅ [SUCCESS] $1"
}

log_error() {
    echo "❌ [ERROR] $1"
}

log_info "Docker 배포 시작..."

# 1. Docker Compose 파일 확인
if [ ! -f "$COMPOSE_FILE" ]; then
    log_error "docker-compose.yml 파일을 찾을 수 없습니다."
    exit 1
fi
log_success "docker-compose.yml 확인됨"

# 2. 환경 파일 확인
if [ ! -f ".env" ]; then
    log_error ".env 파일이 필요합니다."
    exit 1
fi
log_success ".env 파일 확인됨"

# 3. 기존 이미지 확인
log_info "기존 컨테이너 상태 확인..."
docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps

# 4. 이미지 빌드
log_info "이미지 빌드 중..."
docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" build --no-cache

log_success "이미지 빌드 완료"

# 5. 컨테이너 시작
log_info "컨테이너 시작 중..."
docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" up -d

log_success "컨테이너 시작 완료"

# 6. 서비스 상태 확인
log_info "서비스 상태 확인..."
sleep 3  # 서비스 초기화 시간
docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps

# 7. 헬스 체크
log_info "API 헬스 체크..."
max_retries=10
retry_count=0

while [ $retry_count -lt $max_retries ]; do
    if curl -s http://localhost:5000/api/health > /dev/null; then
        log_success "API 헬스 체크 통과"
        break
    fi
    
    retry_count=$((retry_count + 1))
    if [ $retry_count -eq $max_retries ]; then
        log_error "API 헬스 체크 실패. 로그 확인:"
        docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" logs app
        exit 1
    fi
    
    echo "  재시도 중... ($retry_count/$max_retries)"
    sleep 2
done

# 8. 배포 완료 정보
echo ""
echo "═════════════════════════════════════"
echo "🎉 Docker 배포 완료!"
echo "═════════════════════════════════════"
echo ""
echo "📍 서비스 엔드포인트:"
echo "  • Flask API: http://localhost:5000"
echo "  • Vite Frontend: http://localhost:3000"
echo "  • Elasticsearch: http://localhost:9200"
echo ""
echo "🔍 유용한 명령어:"
echo "  • 로그 확인: docker-compose logs -f"
echo "  • 서비스 중지: docker-compose down"
echo "  • 재시작: docker-compose restart"
echo ""
echo "════════════════════════════════════"
