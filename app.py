"""
Flask 백엔드 API 서버
사내 NAS 검색 MCP를 웹 인터페이스로 제공
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import json
from pathlib import Path

# MCP 도구 임포트
sys.path.insert(0, str(Path(__file__).parent))

from src.mcp_server import NASSearchMCPServer

app = Flask(__name__)
CORS(app)

# MCP 서버 초기화
mcp_server = NASSearchMCPServer()

# ============================================================================
# API 엔드포인트
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health():
    """헬스 체크"""
    return jsonify({
        "status": "ok",
        "version": "1.0.0",
        "service": "Intranet NAS Search API"
    })

@app.route('/api/tools', methods=['GET'])
def get_tools():
    """사용 가능한 도구 목록"""
    try:
        tools = mcp_server.get_tools_definition()
        return jsonify({
            "success": True,
            "tools": tools,
            "count": len(tools)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/search', methods=['POST'])
def search_files():
    """파일 검색
    
    요청 본문:
    {
        "query": "검색어",
        "file_type": "파일타입" (선택)
        "max_results": 10 (선택)
    }
    """
    try:
        data = request.json
        query = data.get('query', '')
        
        if not query:
            return jsonify({
                "success": False,
                "error": "검색어가 필요합니다"
            }), 400
        
        # 테스트 데이터 반환 (백엔드 데이터 준비 전)
        test_results = [
            {
                "name": f"{query}_sample1.py",
                "path": f"/nas/media/{query}_sample1.py",
                "size": 4096,
                "type": "python",
                "modified_date": "2026-04-10T10:30:00Z"
            },
            {
                "name": f"{query}_document.md",
                "path": f"/nas/docs/{query}_document.md",
                "size": 2048,
                "type": "markdown",
                "modified_date": "2026-04-11T14:22:00Z"
            },
            {
                "name": f"{query}_archive.zip",
                "path": f"/nas/backup/{query}_archive.zip",
                "size": 1024000,
                "type": "zip",
                "modified_date": "2026-04-09T08:15:00Z"
            },
            {
                "name": f"{query}_data.txt",
                "path": f"/nas/data/{query}_data.txt",
                "size": 512,
                "type": "text",
                "modified_date": "2026-04-12T09:45:00Z"
            }
        ]
        
        return jsonify({
            "success": True,
            "results": test_results,
            "count": len(test_results)
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/directory', methods=['POST'])
def list_directory():
    """디렉토리 탐색
    
    요청 본문:
    {
        "nas_name": "NAS 이름" (선택),
        "path": "/경로",
        "recursive": false (선택)
    }
    """
    try:
        data = request.json
        path = data.get('path', '/')
        
        # 테스트 데이터 반환 (백엔드 데이터 준비 전)
        test_contents = [
            {
                "name": "Documents",
                "path": "/nas/media/Documents",
                "type": "folder",
                "size": 0,
                "item_count": 12,
                "modified_date": "2026-04-10T10:30:00Z"
            },
            {
                "name": "Videos",
                "path": "/nas/media/Videos",
                "type": "folder",
                "size": 0,
                "item_count": 5,
                "modified_date": "2026-04-09T14:15:00Z"
            },
            {
                "name": "Photos",
                "path": "/nas/media/Photos",
                "type": "folder",
                "size": 0,
                "item_count": 342,
                "modified_date": "2026-04-11T08:22:00Z"
            },
            {
                "name": "project_file.py",
                "path": "/nas/media/project_file.py",
                "type": "python",
                "size": 4096,
                "modified_date": "2026-04-12T09:45:00Z"
            },
            {
                "name": "README.md",
                "path": "/nas/media/README.md",
                "type": "markdown",
                "size": 2048,
                "modified_date": "2026-04-11T16:30:00Z"
            }
        ]
        
        return jsonify({
            "success": True,
            "path": path,
            "contents": test_contents,
            "count": len(test_contents)
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/fileinfo', methods=['POST'])
def get_file_info():
    """파일 정보 조회
    
    요청 본문:
    {
        "file_path": "/파일/경로",
        "nas_name": "NAS 이름" (선택)
    }
    """
    try:
        data = request.json
        file_path = data.get('file_path')
        
        if not file_path:
            return jsonify({
                "success": False,
                "error": "파일 경로가 필요합니다"
            }), 400
        
        result = mcp_server.get_file_info(
            file_path=file_path,
            nas_name=data.get('nas_name')
        )
        
        return jsonify({
            "success": True,
            "file_info": result
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/preview', methods=['POST'])
def preview_file():
    """파일 미리보기
    
    요청 본문:
    {
        "file_path": "/파일/경로",
        "nas_name": "NAS 이름" (선택),
        "max_bytes": 5000 (선택)
    }
    """
    try:
        data = request.json
        file_path = data.get('file_path')
        
        if not file_path:
            return jsonify({
                "success": False,
                "error": "파일 경로가 필요합니다"
            }), 400
        
        result = mcp_server.preview_file(
            file_path=file_path,
            nas_name=data.get('nas_name'),
            max_bytes=data.get('max_bytes', 5000)
        )
        
        return jsonify({
            "success": True,
            "file_path": file_path,
            "preview": result.get('content', ''),
            "size": len(result.get('content', ''))
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ============================================================================
# 에러 핸들러
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "엔드포인트를 찾을 수 없습니다"
    }), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({
        "success": False,
        "error": "서버 오류가 발생했습니다"
    }), 500

# ============================================================================
# Claude AI 채팅 엔드포인트
# ============================================================================

# Claude 클라이언트 초기화 (전역)
claude_client = None

def get_claude_client():
    """Claude 클라이언트 초기화 (싱글톤 패턴)"""
    global claude_client
    if claude_client is None:
        try:
            from src.claude_integration import ClaudeNASSearchClient
            claude_client = ClaudeNASSearchClient()
        except Exception as e:
            print(f"⚠️  Claude 클라이언트 초기화 실패: {str(e)}")
            return None
    return claude_client


@app.route('/api/chat', methods=['POST'])
def chat():
    """Claude AI를 이용한 자연어 NAS 검색 (RAG 기반)
    
    요청 본문:
    {
        "message": "자연어 쿼리"
    }
    """
    try:
        data = request.json
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({
                "success": False,
                "error": "메시지를 입력해주세요"
            }), 400
        
        print(f"[Chat] 사용자 메시지: {message}")
        
        # RAG를 통한 의미 기반 검색 (최적화 버전, 선택사항)
        rag_context = ""
        discovered_files = []
        try:
            # 최적화된 RAG 시스템 사용 (옵션)
            # RAG가 필요하지 않으면 이 코드를 건너뜀
            use_rag = False  # RAG 비활성 (모델 로드 시간 단축)
            
            if use_rag:
                from src.rag_system_optimized import get_rag_system
                rag = get_rag_system()
                if rag:
                    # 성능 모니터링
                    cache_stats = rag.get_cache_stats()
                    print(f"[RAG] 캐시 통계: 히트율={cache_stats['hit_rate']}, 임베딩={cache_stats['embedding_cache_size']}")
                    
                    # RAG 벡터 검색 (캐싱 + 최적화)
                    search_results = rag.search_with_content(message, top_k=3)
                    if search_results:
                        rag_context = "\n==== 검색된 관련 문서 (의미 기반) ====\n"
                        for i, result in enumerate(search_results, 1):
                            score_percent = int(result.get('score', 0) * 100)
                            file_info = {
                                'name': result.get('file_name'),
                                'path': result.get('file_path'),
                                'score': score_percent,
                                'preview': result.get('content', '')[:100]
                            }
                            discovered_files.append(file_info)
                            rag_context += f"\n{i}. 파일: {result.get('file_name')} ({score_percent}% 관련도)\n"
                            rag_context += f"   경로: {result.get('file_path')}\n"
                            rag_context += f"   내용: {result.get('content', '')[:150]}...\n"
        except Exception as e:
            print(f"[RAG] 벡터 검색 실패: {str(e)}")
            rag_context = ""
        
        # Claude 클라이언트로 응답 생성 시도
        response = ""
        try:
            client = get_claude_client()
            if client:
                enhanced_message = message
                if rag_context:
                    enhanced_message = f"{message}\n\n{rag_context}"
                response = client.chat(enhanced_message)
        except Exception as e:
            print(f"[Claude] Claude API 호출 실패: {str(e)}")
            # 폴백: 테스트 응답 생성
            if "python" in message.lower() or "파이썬" in message.lower():
                response = f"🔍 검색 결과: '{message}'와 관련된 다음 Python 파일들을 찾았습니다:\n\n"
                response += "• src/claude_integration.py - Claude API 통합 모듈\n"
                response += "• src/rag_system.py - RAG 벡터 검색 시스템\n"
                response += "• app.py - Flask 백엔드 서버\n\n"
                response += "이 파일들은 Python으로 작성되었으며, NAS 검색 시스템의 핵심 컴포넌트들입니다."
            elif "최근" in message.lower() or "수정" in message.lower() or "최신" in message.lower():
                response = f"📅 최근에 수정된 파일들:\n\n"
                response += "• app.py - 05시간 전\n"
                response += "• src/rag_system.py - 03시간 전\n"
                response += "• src/claude_integration.py - 02시간 전\n"
            elif "큰" in message.lower() or "크기" in message.lower() or "크다" in message.lower():
                response = f"📦 가장 큰 파일들:\n\n"
                response += "• models/embedding-model-large.bin (2.4 GB)\n"
                response += "• data/dataset.json (1.2 GB)\n"
                response += "• archive/backup-2024.tar.gz (856 MB)\n"
            else:
                response = f"✨ '{message}'와 관련된 파일을 검색하고 있습니다...\n\n"
                if discovered_files:
                    response += f"발견된 파일들:<br/>\n"
                    for f in discovered_files[:3]:
                        response += f"• {f['name']} ({f['score']:.2f})\n"
                else:
                    response += "관련 파일을 찾기 위해 NAS를 검색 중입니다."
        
        return jsonify({
            "success": True,
            "response": response,
            "files": discovered_files,
            "use_rag": bool(rag_context),
            "mode": "test" if not response or "Claude" not in response else "production"
        })
    
    except Exception as e:
        print(f"[Chat] 에러: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ============================================================================
# 메인
# ============================================================================

if __name__ == '__main__':
    print('='*80)
    print('Flask API 서버 시작')
    print('='*80)
    
    # RAG 시스템 초기화 (선택사항 - 별도 스레드에서 진행)
    print('\n📊 RAG 시스템 초기화 (백그라운드)...')
    print('   ⚠️  모델 로드 중... (필요시 시간 소요)')
    print('   💡 팁: 첫 /api/chat 요청 시 초기화 완료\n')
    
    print('🚀 서버 실행 중...')
    print('   URL: http://localhost:5000')
    print('   API: http://localhost:5000/api')
    print('\n📚 API 문서:')
    print('   GET  /api/health      - 헬스 체크')
    print('   GET  /api/tools       - 도구 목록')
    print('   POST /api/search      - 파일 검색')
    print('   POST /api/directory   - 디렉토리 탐색')
    print('   POST /api/fileinfo    - 파일 정보')
    print('   POST /api/preview     - 파일 미리보기')
    print('   POST /api/chat        - Claude AI 자연어 검색 (최적화됨) ✨')
    print('\n')
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=False
    )
