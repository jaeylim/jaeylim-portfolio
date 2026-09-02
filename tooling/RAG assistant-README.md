> 참고: 기존 tooling/README.md의 RAG 어시스턴트 항목 세부 사항

### CSAP 증적자료 체크리스트 RAG 어시스턴트
CSAP 인증 사후평가 증적자료 체크리스트를 기반으로, 통제항목에 대해 질의하면
관련 항목을 검색(Retrieval)하여 그 내용만 근거로 답변을 생성(Generation)하는
간단한 RAG 파이프라인.

### 배경
- CSAP 사후평가 대응 중, 증적자료 체크리스트 항목이 많아 "이 통제항목엔 어떤
  증적이 필요하지?" 를 빠르게 찾기 위한 목적
- GuardDuty AI triage 프로젝트(Bedrock Lambda 파이프라인)에서 확보한 Bedrock
  활용 경험을, 이번엔 RAG 구조로 확장해서 적용

### 아키텍처
```
증적자료 체크리스트.xlsx
        │  (1_extract_checklist.py)
        ▼
   checklist.json  (범주/분야/통제항목/필요증적/비고 구조화)
        │  (2_build_index.py, Titan Embeddings)
        ▼
embeddings.npy + checklist_with_text.json
        │
        │  질문 입력
        ▼
   (3_query_rag.py)
   질문 임베딩 → 코사인 유사도 Top-K 검색 → Nova에 컨텍스트로 전달 → 답변
```

### 설계 결정
- **벡터DB 대신 numpy 배열 사용**: 체크리스트 항목이 ~50개 수준이라 OpenSearch
  Serverless 같은 실제 벡터 인덱스는 오버스펙. 항목 수가 커지면(수백~수천) 그때
  OpenSearch(Bedrock Knowledge Base 연동) 또는 FAISS로 전환하는 게 다음 단계.
- **생성 모델은 Nova**: GuardDuty AI triage에서 Claude Haiku 시도 시 에러가
  나서 Nova로 전환했던 경험을 그대로 재사용.
- **답변 범위를 체크리스트 내용으로 한정**: 프롬프트에서 "참고 항목에 없으면
  모른다고 답하라"고 명시해 환각(hallucination) 방지.

### 실행 방법
```bash
pip install -r requirements.txt

# 1. 체크리스트 파싱 (엑셀 파일명은 실제 파일명으로 맞출 것)
python 1_extract_checklist.py

# 2. 임베딩 인덱스 생성 (Bedrock 호출, 회사 테스트 계정 자격증명 필요)
python 2_build_index.py

# 3. 질의
python 3_query_rag.py "네트워크 분리 관련해서 어떤 증적이 필요해?"
```

### 다음 확장 아이디어 (스트레치)
- 체크리스트 외 실제 증적 문서(정책서, 결과보고서)까지 색인 범위 확대
- 여러 인증 기준(CSAP, ISMS-P, PCI-DSS) 통합 검색
- 항목 수 증가 시 OpenSearch Serverless 기반 Bedrock Knowledge Base로 전환
