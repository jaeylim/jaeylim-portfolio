# GuardDuty AI Triage 확장

기존 GuardDuty → EventBridge → SNS 기본 탐지 파이프라인에, Amazon Bedrock을 연동해 finding에 대한 AI 기반 위협 요약·우선순위 판단을 추가한 확장 작업.

## 배경

기존 파이프라인은 GuardDuty finding을 EventBridge로 라우팅해 SNS로 원본 알림을 발송하는 구조였다. 다만 원본 finding은 JSON 형태의 기술적 정보(type, severity, resource 등)만 담고 있어, 담당자가 위협의 실제 의미와 대응 우선순위를 판단하려면 매번 GuardDuty 콘솔에서 상세 내용을 추가로 확인해야 했다. 이 확장 작업은 Lambda와 Bedrock을 파이프라인 중간에 추가해, finding 발생 시 자동으로 위협 요약과 권장 조치까지 함께 전달되도록 개선한 것이다.

## 아키텍처

```
GuardDuty (탐지)
  → EventBridge (severity ≥ 7 필터링)
    → Lambda (finding 파싱 → Bedrock 호출)
      → Amazon Bedrock (Nova Micro, 위협 요약·우선순위 판단)
    → SNS (가공된 결과 발송)
```

## 작업 내용

### 1. EventBridge 필터링 강화
기존 이벤트 패턴에 severity 기준 필터를 추가해, 낮은 심각도 finding까지 전부 처리 대상에 넣지 않도록 설계했다.

```json
{
  "source": ["aws.guardduty"],
  "detail-type": ["GuardDuty Finding"],
  "detail": {
    "severity": [{ "numeric": [">=", 7] }]
  }
}
```

무분별하게 전체 finding을 AI 처리로 넘기지 않고, High(7.0 이상) 등급만 우선 대상으로 삼은 설계 판단.

### 2. SNS 알림 가독성 개선 (Input Transformer)
Lambda 연동 이전 단계에서, EventBridge → SNS 직결 구조의 알림이 원본 JSON 그대로 발송되어 가독성이 떨어지는 문제를 발견. Input Transformer로 필요한 필드만 추출해 사람이 읽기 쉬운 형태로 재구성했다.

- 줄바꿈이 이메일 클라이언트에서 `\n` 문자 그대로 노출되는 문제 발생 → 각 줄을 개별 문자열로 분리해 실제 개행이 유지되도록 처리

### 3. Lambda + Amazon Bedrock 연동
`lambda_function.py` 참고. GuardDuty finding을 파싱해 Bedrock에 위협 요약을 요청하고, 결과를 SNS로 발송하는 구조.

**모델 선정 트러블슈팅**
- Anthropic Claude(Haiku 3, Haiku 4.5 모두) 호출 시 `Access to this model is not available for channel program accounts` 에러 발생 — 사용 중인 AWS 계정이 파트너/리셀러 채널 프로그램 소속이라 Anthropic 모델의 Marketplace 라이선싱 승인이 제한된 것으로 확인
- Amazon Nova Micro로 전환해 정상 동작 확인. 다만 on-demand 방식으로는 호출 불가하여 리전 그룹형 inference profile ID(`apac.amazon.nova-micro-v1:0`) 사용 필요
- 계정 종류에 따라 사용 가능한 파운데이션 모델이 다를 수 있다는 것을 실제 트러블슈팅으로 확인한 경험

### 4. 검증 결과
Lambda 함수를 테스트 이벤트로 직접 실행해 Bedrock(Nova Micro) 호출과 SNS 발송까지 전체 흐름이 정상 동작하는 것을 확인했다. AI가 생성한 응답은 위협 요약, 우선순위 판단, 권장 조치 3단 구조로 반환되며, 실제 이메일 수신까지 확인됨.

## 진행 예정
- EventBridge Rule의 target을 SNS에서 Lambda로 전환한 뒤, GuardDuty finding 발생 시 자동 트리거되는 end-to-end 흐름 검증 (수동 Lambda 실행까지는 확인, 자동 트리거 연동은 추가 디버깅 필요)
