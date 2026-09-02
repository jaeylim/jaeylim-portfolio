"""
Step 3: RAG 질의 응답

흐름:
  질문 -> Titan Embeddings로 벡터화
       -> 저장된 체크리스트 벡터들과 코사인 유사도 계산
       -> 상위 K개 항목만 추려서 프롬프트에 삽입 (Retrieval)
       -> Nova가 그 항목들만 근거로 답변 생성 (Generation)

GuardDuty AI triage 때와 동일하게 Bedrock의 amazon.nova-lite-v1:0 사용.
(참고: 처음에 anthropic.claude-3-haiku 로 시도했다가 에러가 나서 Nova로 전환했던
 그 트러블슈팅 경험 그대로 재사용)
"""
import json
import sys
import boto3
import numpy as np

REGION = "us-east-1"
EMBED_MODEL_ID = "amazon.titan-embed-text-v2:0"
GEN_MODEL_ID = "amazon.nova-lite-v1:0"
TOP_K = 3

bedrock = boto3.client("bedrock-runtime", region_name=REGION)


def embed_text(text: str) -> list[float]:
    """2_build_index.py 와 동일한 임베딩 함수 (질문도 같은 모델로 벡터화해야 함)"""
    body = json.dumps({"inputText": text})
    resp = bedrock.invoke_model(
        modelId=EMBED_MODEL_ID,
        body=body,
        contentType="application/json",
        accept="application/json",
    )
    result = json.loads(resp["body"].read())
    return result["embedding"]


def cosine_sim(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a_norm = a / (np.linalg.norm(a) + 1e-8)
    b_norm = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-8)
    return b_norm @ a_norm


def retrieve(question: str, rows: list[dict], vectors: np.ndarray, k=TOP_K):
    q_vec = np.array(embed_text(question), dtype=np.float32)
    sims = cosine_sim(q_vec, vectors)
    top_idx = np.argsort(-sims)[:k]
    return [(rows[i], float(sims[i])) for i in top_idx]


def generate_answer(question: str, retrieved: list[tuple[dict, float]]) -> str:
    context = "\n\n".join(
        f"[관련도 {score:.2f}] {row['_chunk_text']}" for row, score in retrieved
    )
    prompt = f"""당신은 CSAP(클라우드 보안 인증) 증적자료 체크리스트를 안내하는 어시스턴트입니다.
아래 [참고 항목]에 있는 내용만 근거로 답변하세요. 참고 항목에 없는 내용은 추측하지 말고
"체크리스트에서 해당 정보를 찾을 수 없습니다"라고 답하세요.

[참고 항목]
{context}

[질문]
{question}

[답변]"""

    body = json.dumps({
        "messages": [{"role": "user", "content": [{"text": prompt}]}],
        "inferenceConfig": {"maxTokens": 500, "temperature": 0.2},
    })
    resp = bedrock.invoke_model(
        modelId=GEN_MODEL_ID,
        body=body,
        contentType="application/json",
        accept="application/json",
    )
    result = json.loads(resp["body"].read())
    return result["output"]["message"]["content"][0]["text"]


if __name__ == "__main__":
    with open("checklist_with_text.json", encoding="utf-8") as f:
        rows = json.load(f)
    vectors = np.load("embeddings.npy")

    question = " ".join(sys.argv[1:]) or input("질문을 입력하세요: ")

    retrieved = retrieve(question, rows, vectors)
    print("\n--- 검색된 관련 항목 ---")
    for row, score in retrieved:
        print(f"({score:.2f}) {row['control_item']} -> {row['evidence_required']}")

    answer = generate_answer(question, retrieved)
    print("\n--- 답변 ---")
    print(answer)
