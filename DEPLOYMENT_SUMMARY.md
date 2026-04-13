# 배포 자동화 설정 요약

## 📂 생성된 파일 목록

### 스크립트 (3개)
```
deploy.sh              → Linux/Mac 로컬 배포 자동화
deploy.bat             → Windows 로컬 배포 자동화
docker-deploy.sh      → Docker 배포 오케스트레이션
k8s-deploy.sh         → Kubernetes 배포 오케스트레이션
```

### Docker 설정 (5개)
```
docker-compose.yml           → 개발 환경 컨테이너 설정
docker-compose.prod.yml      → 프로덕션 환경 컨테이너 설정
Dockerfile                   → Python 백엔드 이미지
frontend/Dockerfile.dev      → Vue 개발 이미지
frontend/Dockerfile.prod     → Vue 프로덕션 이미지 (Nginx)
frontend/nginx.conf          → Nginx 역프록시 설정
```

### Kubernetes 설정 (1개)
```
k8s-deployment.yaml         → 완전한 K8s 리소스 정의
                             (Namespace, Deployment, Service, Ingress, PVC)
```

### CI/CD 설정 (1개)
```
.github/workflows/ci-cd.yml  → GitHub Actions 자동화 워크플로우
                             (테스트, 빌드, 스캔, 배포)
```

### 문서 (2개)
```
DEPLOY_COMPLETE.md          → 완전한 배포 가이드
DEPLOYMENT_SUMMARY.md       → 배포 설정 요약 (이 파일)
```

---

## 🎯 배포 옵션별 특징

### 1️⃣ 로컬 배포 (deploy.sh / deploy.bat)
**대상**: 개발자 머신, 로컬 테스트

**실행**:
```bash
# Linux/Mac
chmod +x deploy.sh && ./deploy.sh

# Windows
deploy.bat
```

**포함 기능**:
- ✅ 환경 설정 자동 확인
- ✅ Python venv 생성/활성화
- ✅ 의존성 자동 설치
- ✅ 단위 테스트 실행
- ✅ 필요한 디렉토리 자동 생성
- ✅ 권한 설정

**장점**:
- 가장 간단
- 빠른 개발 사이클
- 직접적인 디버깅 가능

**시작 명령**:
```bash
# 백엔드
source venv/bin/activate
python app.py

# 프론트엔드 (새 터미널)
cd frontend
npm run dev

# 크롤러 (선택)
python -m src.crawler
```

---

### 2️⃣ Docker 배포 (docker-compose.yml)
**대상**: 개발팀, 스테이징, 프로덕션 준비환경

**실행**:
```bash
chmod +x docker-deploy.sh
./docker-deploy.sh
```

**포함 기능**:
- ✅ Elasticsearch 자동 실행
- ✅ Flask 백엔드 컨테이너
- ✅ Vite 프론트엔드 개발 서버
- ✅ 네트워크 자동 설정
- ✅ 헬스체크 설정
- ✅ 자동 재시작

**포트**:
- Flask API: 5000
- Vite Dev: 3000
- Elasticsearch: 9200

**서비스 확인**:
```bash
docker-compose ps
docker-compose logs -f app
```

**프로덕션 버전** (docker-compose.prod.yml):
- Elasticsearch 보안 활성화 (xpack)
- 다중 인스턴스 배포 (2+ replica)
- Nginx 리버스 프록시
- 볼륨 로깅
- 자동 재시작 정책

---

### 3️⃣ Kubernetes 배포 (k8s-deployment.yaml)
**대상**: 프로덕션 운영환경, 대규모 배포

**사전 요구사항**:
- kubectl 설치
- Kubernetes 클러스터 연결
- docker registry 접근 권한

**실행**:
```bash
# 환경 변수 설정
export CLAUDE_API_KEY="..."
export GEMINI_API_KEY="..."
export ELASTICSEARCH_PASSWORD="..."

chmod +x k8s-deploy.sh
./k8s-deploy.sh
```

**포함 기능**:
- ✅ Namespace 격리 (nas-search)
- ✅ Elasticsearch StatefulSet
- ✅ Flask App Deployment (2 replica)
- ✅ Service 노출
- ✅ Ingress 라우팅
- ✅ PersistentVolume 저장소
- ✅ 자동 헬스체크
- ✅ 리소스 제한

**리소스 사용**:
- Elasticsearch: 512Mi-1Gi RAM, 250-500m CPU
- Flask App: 256Mi-512Mi RAM, 250-500m CPU

**상태 확인**:
```bash
kubectl get pods -n nas-search
kubectl get services -n nas-search
kubectl logs -l app=nas-search-app -n nas-search -f
```

---

### 4️⃣ CI/CD 파이프라인 (.github/workflows/ci-cd.yml)
**대상**: GitHub 저장소, 자동 테스트 & 배포

**트리거**:
- Push to main/develop
- Pull requests

**자동 실행 단계**:

1. **코드 품질 검사**
   - flake8 (스타일 체크)
   - pylint (정적 분석)
   - black (포매팅)

2. **백엔드 테스트**
   - pytest 테스트 실행
   - 커버리지 보고

3. **프론트엔드 테스트**
   - npm linting
   - 빌드 검증

4. **Docker 이미지 빌드** (성공 시)
   - 이미지 빌드
   - Registry 푸시

5. **보안 스캔** Trivy)
   - 취약점 검사
   - SARIF 리포트

6. **자동 배포** (main 브랜치만)
   - Kubernetes 이미지 업데이트

---

## 📊 배포 환경 비교표

| 특성 | 로컬 | Docker | Kubernetes |
|------|------|--------|-----------|
| 설정 복잡도 | ⭐ | ⭐⭐ | ⭐⭐⭐ |
| 환경 일관성 | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| 확장성 | ⭐ | ⭐⭐ | ⭐⭐⭐ |
| 가용성 | ⭐ | ⭐⭐ | ⭐⭐⭐ |
| 개발 속도 | ⭐⭐⭐ | ⭐⭐ | ⭐ |
| 프로덕션 준비 | ⭐ | ⭐⭐ | ⭐⭐⭐ |

---

## 🔄 권장 배포 플로우

```
1. 개발 단계
   ↓
   로컬 배포 (deploy.sh/deploy.bat)
   ↓
   
2. 팀 공유 단계
   ↓
   Docker 배포 (docker-compose.yml)
   ↓
   
3. 스테이징 단계
   ↓
   Docker 프로덕션 (docker-compose.prod.yml)
   ↓
   
4. 운영 단계
   ↓
   Kubernetes 배포 (CI/CD와 연동)
   ↓
   
5. 모니터링 & 유지보수
   ↓
   로그 & 메트릭 수집
```

---

## 🚀 첫 배포하기

### 단계 1: 환경 준비
```bash
# .env 파일 작성
CLAUDE_API_KEY="sk-..."
GEMINI_API_KEY="AIz..."
ELASTICSEARCH_PASSWORD="password123"
NAS_PATH="/mnt/nas"
```

### 단계 2: 선택한 배포 방식 실행

**개발자용**:
```bash
./deploy.sh
```

**팀 공유**:
```bash
./docker-deploy.sh
```

**프로덕션**:
```bash
./k8s-deploy.sh
```

### 단계 3: 검증
```bash
# API 헬스 체크
curl http://localhost:5000/api/health

# UI 접근
http://localhost:3000
# 또는
http://localhost:5000
```

---

## 📈 성능 및 확장성

### 로컬
- CPU: 단일 코어 사용
- 메모리: 2GB 이상 권장
- 동시 사용자: 1-5명

### Docker
- CPU: 모든 코어 활용 가능
- 메모리: 4GB 이상 권장
- 동시 사용자: 10-50명

### Kubernetes
- CPU: 클러스터 크기에 따라 확장
- 메모리: 자동 스케일링
- 동시 사용자: 100+ 명

---

## 🔐 배포 체크리스트

배포 전:
- [ ] Python 3.12+ 설치 확인
- [ ] Node.js 20+ 설치 확인 (프론트엔드 필요)
- [ ] Docker 설치 확인 (Docker 배포용)
- [ ] kubectl 설치 확인 (K8s 배포용)
- [ ] .env 파일 설정 완료
- [ ] NAS 경로 접근 권한 확인
- [ ] 필요한 포트 개방 확인 (5000, 3000, 9200)

배포 후:
- [ ] 서비스 실행 확인
- [ ] API /health 응답 확인
- [ ] UI 접근 가능 확인
- [ ] 파일 검색 기능 테스트
- [ ] 로그 생성 확인

---

## 💡 팁

1. **개발 중**: 로컬 배포로 빠른 사이클 유지
2. **테스트**: Docker로 환경 일관성 보장
3. **스테이징**: Docker Prod로 프로덕션 시뮬레이션
4. **운영**: Kubernetes로 자동화된 관리

---

## 📞 지원

배포 문제 발생 시:
1. 해당 스크립트의 로그 확인
2. 서비스 상태 확인 (ps, docker ps, kubectl get pods)
3. 방화벽/포트 설정 확인
4. 환경 변수 설정 재확인

---

**배포 자동화 완전히 준비됨! ✅**
