# 🚀 배포 체크리스트 (Deployment Checklist)

**프로젝트**: 사내 NAS 검색 MCP  
**작성일**: 2026-04-12  
**최종 확인**: [완료 날짜 입력]

---

## 📋 배포 전 준비 (Pre-Deployment)

### 1️⃣ 환경 설정 확인

- [ ] `.env` 파일이 `.gitignore`에 있는지 확인
- [ ] `.env.example` 파일이 Git에 커밋되었는지 확인
- [ ] 민감한 정보(비밀번호, API 키)가 소스 코드에 없는지 확인

**확인 명령어:**
```bash
git status
cat .gitignore | grep ".env"
grep -r "password\|api_key\|secret" src/ --exclude-dir=__pycache__
```

---

### 2️⃣ 의존성 확인

- [ ] `requirements.txt`가 모든 의존성을 포함하는지 확인
- [ ] Python 최소 버전 3.10 이상 명시
- [ ] 각 패키지 버전 범위 지정되어 있는지 확인

**확인 명령어:**
```bash
cat requirements.txt
pip list | grep -E "elasticsearch|anthropic|google-generativeai|flask"
```

---

### 3️⃣ 문서 준비

- [ ] `README.md` - 프로젝트 개요, 설치 방법, 실행 방법 포함
- [ ] `.env.example` - 모든 필수 환경 변수 포함
- [ ] `DEPLOYMENT.md` - 배포 가이드 (별도 생성 권장)
- [ ] `ARCHITECTURE.md` - 시스템 아키텍처 설명
- [ ] `API.md` - API 엔드포인트 문서

**생성할 파일:**
- [x] DEPLOYMENT.md (이 파일 이후 생성)

---

## 🖥️ 로컬 테스트 (Local Testing)

### 4️⃣ 단위 테스트

```bash
# 모든 테스트 실행
pytest tests/ -v

# 특정 테스트만 실행
pytest tests/test_elasticsearch.py -v
pytest tests/test_mcp_integration.py -v
```

- [ ] 모든 테스트 통과 (96.8% 이상)
- [ ] 경고 없음
- [ ] 테스트 커버리지 70% 이상

---

### 5️⃣ 통합 테스트

```bash
# Elasticsearch 연결 테스트
python test_elasticsearch.py

# MCP 도구 통합 테스트
python test_mcp_integration_all_tools.py

# API 엔드포인트 테스트
python test_api.py

# Claude/Gemini 통합 테스트
python test_both_apis.py
```

- [ ] Elasticsearch 연결 성공
- [ ] 모든 MCP 도구 작동
- [ ] API 응답 정상 (200 상태 코드)
- [ ] AI API 응답 정상

---

### 6️⃣ 성능 테스트

```bash
# 검색 성능 벤치마크
python benchmark_optimization.py

# Elasticsearch 최적화 체크
python check_elasticsearch.py
```

- [ ] 평균 응답 시간 < 500ms
- [ ] 검색 성능 최소 10배 이상 향상
- [ ] 캐시 히트율 > 50%

---

## 🌐 서버 배포 체크리스트 (Server Deployment)

### 7️⃣ 서버 준비

**필수 요구사항:**
- [ ] Linux/Windows Server OS (권장: Ubuntu 20.04+)
- [ ] Python 3.10 이상 설치
- [ ] Elasticsearch 8.x 설치 및 실행 중
- [ ] 포트 개방: 5000 (Flask), 3000 (Vite), 9200 (Elasticsearch)
- [ ] 최소 2GB 여유 RAM
- [ ] 최소 10GB 여유 디스크

**설치 확인:**
```bash
python --version
elasticsearch --version
nc -zv localhost 9200
```

---

### 8️⃣ 환경 변수 설정 (서버용)

**필수 환경 변수:**
```bash
# .env 파일 생성 (서버에서)
cat > .env << EOF
# NAS 정보 (실제 값으로 변경)
NAS_HOST_1=192.168.x.x
NAS_SHARE_1=공유폴더명
NAS_USERNAME_1=도메인\사용자명
NAS_PASSWORD_1=비밀번호

# Elasticsearch (서버 실제 IP)
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_USERNAME=elastic
ELASTICSEARCH_PASSWORD=실제_비밀번호

# AI API (선택)
ANTHROPIC_API_KEY=sk-...
GOOGLE_API_KEY=...

# 애플리케이션
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
EOF
```

- [ ] `.env` 파일 생성 완료
- [ ] 파일 권한 설정: `chmod 600 .env` (Linux)
- [ ] `.env` 파일이 Git에 추적되지 않는지 확인

---

### 9️⃣ 의존성 설치

```bash
# Python 가상환경 생성
python -m venv venv

# 활성화
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 설치 확인
pip list
```

- [ ] venv 생성 및 활성화
- [ ] 모든 의존성 설치 (pip list 확인)
- [ ] 패키지 버전 충돌 없음

---

### 🔟 서비스 시작

#### **백엔드 Flask 서버**
```bash
# 개발 모드
python app.py

# 프로덕션 모드 (Gunicorn 권장)
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

- [ ] Flask 서버 포트 5000에서 실행
- [ ] http://localhost:5000/api/health 응답 확인

#### **프론트엔드 Vite 서버**
```bash
# Node.js 설치 확인
node --version
npm --version

# 의존성 설치
npm install

# 개발 서버
npm run dev

# 프로덕션 빌드
npm run build
npm run preview
```

- [ ] Vite 개발 서버 포트 3000에서 실행
- [ ] http://localhost:3000 접근 가능

#### **배경 크롤러 (선택)**
```bash
# 백그라운드 프로세스로 실행
nohup python -m src.crawler > crawler.log 2>&1 &

# 또는 systemd 서비스로 등록 (Linux)
sudo systemctl start nas-crawler
sudo systemctl enable nas-crawler
```

- [ ] 크롤러 프로세스 실행 중
- [ ] 크롤러 로그 생성 확인

---

## ✅ 배포 후 검증 (Post-Deployment Validation)

### 1️⃣1️⃣ 기본 기능 테스트

```bash
# API 헬스 체크
curl http://localhost:5000/api/health

# 도구 목록 조회
curl http://localhost:5000/api/tools

# 테스트 검색
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query":"test"}'
```

- [ ] `/api/health` - 200 OK
- [ ] `/api/tools` - 도구 목록 반환
- [ ] `/api/search` - 검색 결과 반환
- [ ] `/api/chat` - AI 응답 반환

---

### 1️⃣2️⃣ UI 접근 테스트

- [ ] http://localhost:3000 접근 가능
- [ ] 채팅 입력창 표시
- [ ] 예제 질문 표시
- [ ] 메시지 전송 가능
- [ ] 응답 표시

---

### 1️⃣3️⃣ 로깅 확인

```bash
# 로그 파일 생성 확인
ls -la logs/
tail -f logs/nas_search.log

# Flask 로그
tail -f nohup.out (또는 systemd 저널)

# 크롤러 로그
tail -f crawler.log
```

- [ ] 로그 파일 생성됨
- [ ] 에러 없음 (WARN 이상 레벨만 표시)
- [ ] 타임스탬프 정상

---

### 1️⃣4️⃣ 성능 모니터링

```bash
# 리소스 사용량 확인
top  # 또는 htop
ps aux | grep python

# Elasticsearch 상태
curl -s http://localhost:9200/_cluster/health | jq

# 디스크 사용량
df -h
du -sh data/
```

- [ ] CPU 사용률 < 50%
- [ ] 메모리 사용률 < 70%
- [ ] Elasticsearch 상태: green
- [ ] 디스크 여유 > 20%

---

## 🔒 보안 체크 (Security Checklist)

- [ ] `.env` 파일의 권한 설정 (chmod 600)
- [ ] 프로덕션 환경에서 DEBUG=false
- [ ] HTTPS 인증서 설정 (프로덕션)
- [ ] API 인증/인가 구현 (선택)
- [ ] 방화벽 설정 (필요한 포트만 개방)
- [ ] 정기 백업 스크립트 설정

---

## 📊 배포 체크리스트 요약

```
완료도 계산:
선택된 항목 수 / 전체 항목 수 × 100 = ___%

목표: 100% 완료
```

| 섹션 | 항목 수 | 완료 | 미완료 |
|------|--------|------|--------|
| 배포 전 준비 | 6 | _ | _ |
| 로컬 테스트 | 8 | _ | _ |
| 서버 배포 | 6 | _ | _ |
| 배포 후 검증 | 8 | _ | _ |
| 보안 체크 | 6 | _ | _ |
| **합계** | **34** | **_** | **_** |

---

## 🆘 문제 해결 (Troubleshooting)

### Elasticsearch 연결 실패
```bash
# Elasticsearch 상태 확인
curl http://localhost:9200

# 포트 확인
netstat -an | grep 9200

# 재시작
systemctl restart elasticsearch
```

---

### NAS 접근 실패
```bash
# SMB 연결 테스트
smbclient -L //NAS_HOST -U domain\\username

# 권한 확인
smbclient //NAS_HOST/SHARE -U domain\\username
```

---

### API 응답 느림
```bash
# 성능 벤치마크 실행
python benchmark_optimization.py

# 캐시 상태 확인
python -c "from src.rag_system_optimized import get_rag_system; rag = get_rag_system(); print(rag.get_cache_stats())"
```

---

## 📞 지원 연락처

- **기술 문제**: [이슈 트래커]
- **성능 문제**: 성능 벤치마크 로그 첨부
- **보안 문제**: 보안팀 연락

---

## 📝 배포 기록

| 날짜 | 설명 | 담당자 | 상태 |
|------|------|--------|------|
| 2026-04-12 | 초기 배포 | __ | [ ] |
| | | | [ ] |
| | | | [ ] |

---

**최종 확인자**: ______________
**확인 날짜**: ______________
**서명**: ______________
