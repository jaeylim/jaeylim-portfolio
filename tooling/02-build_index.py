"""
Step 2: 체크리스트 각 항목을 임베딩하여 로컬 벡터 인덱스 생성

- 별도 벡터DB(OpenSearch 등) 없이, numpy 배열 + JSON 메타데이터로 충분.
  항목 수가 ~50개 수준이라 이 정도로 MVP는 충분함.
  항목이 수천 개 이상으로 늘어나면 OpenSearch Serverless(Bedrock KB 연동)나
  FAISS 같은 실제 벡터 인덱스로 전환하는 게 맞음 -> 이게 "RAG 확장 계획" 포인트.
"""
import json
import boto3
import numpy as np

REGION = "ap-northeast-2"  
EMBED_MODEL_ID = "amazon.titan-embed-text-v2:0"

bedrock = boto3.client("bedrock-runtime", region_name=REGION)


def embed_text(text: str) -> list[float]:
    body = json.dumps({"inputText": text})
    resp = bedrock.invoke_model(
        modelId=EMBED_MODEL_ID,
        body=body,
        contentType="application/json",
        accept="application/json",
    )
    result = json.loads(resp["body"].read())
    return result["embedding"]


def row_to_text(row: dict) -> str:
    """검색 대상이 될 텍스트 청크 구성"""
    parts = [
        f"범주: {row.get('category') or ''}",
        f"분야: {row.get('domain') or ''}",
        f"통제항목: {row.get('control_item') or ''}",
        f"필요 증적자료: {row.get('evidence_required') or ''}",
    ]
    if row.get("note"):
        parts.append(f"비고: {row['note']}")
    return "\n".join(parts)


if __name__ == "__main__":
    with open("checklist.json", encoding="utf-8") as f:
        rows = json.load(f)

    vectors = []
    for i, row in enumerate(rows):
        text = row_to_text(row)
        vec = embed_text(text)
        vectors.append(vec)
        row["_chunk_text"] = text
        print(f"[{i+1}/{len(rows)}] 임베딩 완료: {row.get('control_item')}")

    np.save("embeddings.npy", np.array(vectors, dtype=np.float32))
    with open("checklist_with_text.json", "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    print("인덱스 생성 완료: embeddings.npy + checklist_with_text.json")
