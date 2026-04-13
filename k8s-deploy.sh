#!/bin/bash
# Kubernetes 배포 스크립트

set -e

# 설정
NAMESPACE="nas-search"
IMAGE_NAME="nas-search-app"
REGISTRY="${REGISTRY:-localhost:5000}"
KUBECONFIG="${KUBECONFIG:-$HOME/.kube/config}"

log_info() {
    echo "ℹ️  [INFO] $1"
}

log_success() {
    echo "✅ [SUCCESS] $1"
}

log_error() {
    echo "❌ [ERROR] $1"
}

# 1. 사전 요구사항 확인
log_info "사전 요구사항 확인..."

if ! command -v kubectl &> /dev/null; then
    log_error "kubectl이 설치되지 않았습니다."
    exit 1
fi

if ! command -v docker &> /dev/null; then
    log_error "Docker가 설치되지 않았습니다."
    exit 1
fi

log_success "필수 도구 확인됨"

# 2. Kubernetes 클러스터 연결 확인
log_info "Kubernetes 클러스터 확인..."
if ! kubectl cluster-info &> /dev/null; then
    log_error "Kubernetes 클러스터에 연결할 수 없습니다."
    exit 1
fi
log_success "클러스터 연결 성공"

# 3. Docker 이미지 빌드
log_info "Docker 이미지 빌드 중..."
docker build -t ${IMAGE_NAME}:latest .
log_success "이미지 빌드 완료"

# 4. 이미지 레지스트리에 푸시 (필요한 경우)
if [ ! -z "$REGISTRY" ] && [ "$REGISTRY" != "localhost:5000" ]; then
    log_info "이미지를 레지스트리에 푸시 중..."
    docker tag ${IMAGE_NAME}:latest ${REGISTRY}/${IMAGE_NAME}:latest
    docker push ${REGISTRY}/${IMAGE_NAME}:latest
    log_success "이미지 푸시 완료"
fi

# 5. 네임스페이스 생성
log_info "네임스페이스 생성..."
kubectl apply -f - <<EOF
apiVersion: v1
kind: Namespace
metadata:
  name: ${NAMESPACE}
EOF
log_success "네임스페이스 생성 완료"

# 6. Secret 생성
log_info "Secret 생성 중..."
kubectl create secret generic nas-search-secrets \
    --from-literal=CLAUDE_API_KEY=${CLAUDE_API_KEY} \
    --from-literal=GEMINI_API_KEY=${GEMINI_API_KEY} \
    --from-literal=ELASTICSEARCH_PASSWORD=${ELASTICSEARCH_PASSWORD} \
    -n ${NAMESPACE} \
    --dry-run=client -o yaml | kubectl apply -f -
log_success "Secret 생성 완료"

# 7. 배포 적용
log_info "Kubernetes 배포 적용 중..."
kubectl apply -f k8s-deployment.yaml
log_success "배포 적용 완료"

# 8. 배포 상태 확인
log_info "배포 상태 확인..."
sleep 5
kubectl rollout status deployment/nas-search-app -n ${NAMESPACE} --timeout=5m

log_success "Kubernetes 배포 성공"

# 9. 배포 정보 출력
echo ""
echo "═══════════════════════════════════════════"
echo "🎉 Kubernetes 배포 완료!"
echo "═══════════════════════════════════════════"
echo ""

echo "📍 서비스 정보:"
kubectl get services -n ${NAMESPACE}

echo ""
echo "📊 Pod 상태:"
kubectl get pods -n ${NAMESPACE}

echo ""
echo "🔍 유용한 명령어:"
echo "  • 로그 확인: kubectl logs -l app=nas-search-app -n ${NAMESPACE} -f"
echo "  • Pod 진입: kubectl exec -it <pod-name> -n ${NAMESPACE} -- bash"
echo "  • 배포 상태: kubectl rollout status deployment/nas-search-app -n ${NAMESPACE}"
echo "  • 배포 제거: kubectl delete namespace ${NAMESPACE}"
echo ""
echo "════════════════════════════════════════════"
