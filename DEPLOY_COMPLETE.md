# 배포 완료 가이드

> **이 문서는 NAS 검색 MCP 프로젝트의 배포 자동화 설정이 완료되었음을 나타냅니다.**

## 📋 배포 자동화 설정 완료 항목

### 1. ✅ 로컬 배포 스크립트
- **deploy.sh** - Linux/Mac용 배포 스크립트
- **deploy.bat** - Windows용 배포 스크립트
- 기능:
  - 환경 설정 자동 확인
  - Python 가상환경 생성/활성화
  - 의존성 자동 설치
  - 자동 테스트 실행
  - 디렉토리 생성 및 권한 설정

### 2. ✅ Docker 컨테이너 배포
- **docker-compose.yml** - 개발 환경
- **docker-compose.prod.yml** - 프로덕션 환경
- **Dockerfile** - Python 백엔드 이미지
- **frontend/Dockerfile.dev** - Vue 개발 이미지
- **frontend/Dockerfile.prod** - Vue 프로덕션 이미지 (Nginx)
- **docker-deploy.sh** - Docker 배포 오케스트레이션 스크립트

### 3. ✅ Kubernetes 배포
- **k8s-deployment.yaml** - Kubernetes 리소스 정의
  - Namespace 생성
  - Elasticsearch Deployment & Service
  - Flask App Deployment & Service (2 replica)
  - Nginx Ingress
  - PersistentVolumeClaim 저장소
- **k8s-deploy.sh** - Kubernetes 배포 스크립트

### 4. ✅ CI/CD 파이프라인
- **.github/workflows/ci-cd.yml** - GitHub Actions 워크플로우
  - 코드 품질 검사 (flake8, pylint, black)
  - 백엔드 테스트 (pytest, coverage)
  - 프론트엔드 테스트 및 빌드
  - Docker 이미지 빌드 및 푸시
  - 보안 스캔 (Trivy)
  - 자동 배포 (main 브랜치)

## 🚀 빠른 시작 가이드

### 옵션 1: 로컬 배포 (권장)

#### Linux/Mac:
```bash
# 권한 설정
chmod +x deploy.sh

# 배포 실행
./deploy.sh
```

#### Windows:
```cmd
# 관리자 권한으로 PowerShell 실행 후
deploy.bat
```

### 옵션 2: Docker 배포

#### 개발 환경:
```bash
# 권한 설정
chmod +x docker-deploy.sh

# 배포 실행
./docker-deploy.sh
```

#### 프로덕션 환경:
```bash
COMPOSE_FILE=docker-compose.prod.yml ./docker-deploy.sh
```

### 옵션 3: Kubernetes 배포

```bash
# 권한 설정
chmod +x k8s-deploy.sh

# 사전 작업: .env 파일 설정
export CLAUDE_API_KEY="your-key"
export GEMINI_API_KEY="your-key"
export ELASTICSEARCH_PASSWORD="your-password"

# 배포 실행
./k8s-deploy.sh
```

## 📦 배포 후 검증

### 1. 서비스 상태 확인
```bash
# 개발 (로컬)
curl http://localhost:5000/api/health
curl http://localhost:3000

# Docker
docker-compose ps
docker-compose logs app

# Kubernetes
kubectl get pods -n nas-search
kubectl get services -n nas-search
```

### 2. API 엔드포인트 테스트
```bash
# 헬스 체크
curl http://localhost:5000/api/health

# 도구 목록
curl http://localhost:5000/api/tools

# 파일 검색
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "python"}'
```

### 3. UI 접근
- 로컬: http://localhost:3000 (또는 5000)
- Docker: http://localhost:3000
- Kubernetes: http://nas-search.example.com

## 🔧 배포 환경별 특징

### 로컬 배포
✅ 장점:
- 가장 간단한 설정
- 빠른 개발 사이클
- 로컬 디버깅 가능

❌ 단점:
- 단일 머신에만 실행
- 하드웨어 의존성 높음

### Docker 배포
✅ 장점:
- 환경 일관성 보장
- 쉬운 확장성
- 개발 → 프로덕션 매끄러운 전환

❌ 단점:
- 추가 학습곡선
- 리소스 오버헤드

### Kubernetes 배포
✅ 장점:
- 프로덕션 수준
- 자동 확장 및 복구
- 높은 가용성
- 롤링 업데이트

❌ 단점:
- 복잡한 설정
- 높은 오버헤드

## 📊 배포 체크리스트

배포 전 확인:
- [ ] .env 파일 설정 완료
- [ ] Elasticsearch 실행 중
- [ ] 필요한 API 키 확보
- [ ] NAS 경로 설정 완료

배포 후 검증:
- [ ] 서비스 정상 실행 확인
- [ ] API 헬스 체크 통과
- [ ] UI 접근 가능
- [ ] 파일 검색 기능 정상 작동

## 🔐 보안 권장사항

1. **환경 변수 관리**
   - .env 파일을 Git에 커밋하지 않음
   - 프로덕션 환경에서는 Kubernetes Secret 사용

2. **SSL/TLS 설정**
   - 프로덕션에서 HTTPS 필수
   - Nginx/Ingress에 인증서 설정

3. **접근 제어**
   - 파이어월 규칙 설정
   - 내부 네트워크 제한

4. **모니터링**
   - 로그 수집 설정
   - 메트릭 모니터링 (Prometheus)

## 📝 로그 확인

### 로컬 배포
```bash
tail -f logs/app.log
```

### Docker
```bash
docker-compose logs -f app
docker-compose logs -f elasticsearch
```

### Kubernetes
```bash
kubectl logs -l app=nas-search-app -n nas-search -f
kubectl logs -l app=elasticsearch -n nas-search -f
```

## 🆘 문제 해결

### 포트 충돌
```bash
# 사용 중인 포트 확인
lsof -i :5000
lsof -i :3000
lsof -i :9200

# 프로세스 종료
kill -9 <PID>
```

### Elasticsearch 연결 실패
```bash
# Elasticsearch 상태 확인
curl http://localhost:9200/_cluster/health

# 로그 확인
docker-compose logs elasticsearch
```

### 권한 오류
```bash
# 파일 권한 수정
chmod 600 .env
chmod -R 755 logs
```

## 📚 추가 참고 자료

- [Docker Compose 문서](https://docs.docker.com/compose/)
- [Kubernetes 문서](https://kubernetes.io/docs/)
- [GitHub Actions 문서](https://docs.github.com/en/actions)
- [Flask 배포 가이드](https://flask.palletsprojects.com/deployment/)
- [Vue 배포 가이드](https://vitejs.dev/guide/build.html)

## ✅ 다음 단계

1. **환경 설정**
   - .env 파일에 API 키 설정
   - NAS 경로 확인

2. **첫 배포**
   - 로컬 배포로 시작 권장
   - 기능 검증 후 Docker/K8s로 확장

3. **모니터링 및 로깅**
   - 로그 수집 설정
   - 성능 모니터링 구성

4. **CI/CD 연동**
   - GitHub 저장소에 코드 푸시
   - 자동 테스트 및 배포 확인

---

**배포 완료! 🎉**

모든 배포 스크립트가 준비되어 있습니다.
원하는 환경에서 배포를 시작하세요!
