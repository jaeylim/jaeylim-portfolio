"""
GuardDuty AI Triage - Lambda Function

GuardDuty finding(EventBridge 경유)을 받아 Amazon Bedrock(Nova Micro)에
위협 요약 및 우선순위 판단을 요청하고, 결과를 SNS로 발송한다.
"""

import json
import boto3

bedrock = boto3.client("bedrock-runtime", region_name="ap-northeast-2")
sns = boto3.client("sns", region_name="ap-northeast-2")

SNS_TOPIC_ARN = "arn:aws:sns:ap-northeast-2:812631270584:guardduty-findings-topic"

# 참고: Anthropic Claude 모델은 계정 종류(channel program account)에 따라
# 접근이 제한될 수 있어, Amazon Nova Micro의 inference profile을 사용함
MODEL_ID = "apac.amazon.nova-micro-v1:0"


def lambda_handler(event, context):
    detail = event.get("detail", {})
    finding_type = detail.get("type", "Unknown")
    severity = detail.get("severity", "Unknown")
    region = detail.get("region", "Unknown")
    resource_type = detail.get("resource", {}).get("resourceType", "Unknown")
    description = detail.get("description", "")

    prompt = f"""다음 AWS GuardDuty 보안 탐지 결과를 분석해서 한국어로 간단히 요약해줘.
이모지는 사용하지 마.

탐지 유형: {finding_type}
심각도: {severity}
리소스: {resource_type}
설명: {description}

아래 형식으로 답변해줘:
1. 위협 요약 (1-2문장)
2. 우선순위 판단 (즉시 대응 필요 / 모니터링 필요 / 낮은 우선순위)
3. 권장 조치 (1-2문장)
"""

    response = bedrock.invoke_model(
        modelId=MODEL_ID,
        body=json.dumps({
            "messages": [
                {"role": "user", "content": [{"text": prompt}]}
            ],
            "inferenceConfig": {"maxTokens": 300}
        })
    )

    result = json.loads(response["body"].read())
    ai_summary = result["output"]["message"]["content"][0]["text"]

    message = f"""GuardDuty AI Triage 결과

탐지 유형: {finding_type}
심각도: {severity}
리전: {region}
리소스: {resource_type}

--- AI 분석 ---
{ai_summary}
"""

    sns.publish(
        TopicArn=SNS_TOPIC_ARN,
        Subject="GuardDuty AI Triage 알림",
        Message=message
    )

    return {"statusCode": 200, "body": "처리 완료"}
