### 01. GuardDuty 기반 위협 탐지
GuardDuty를 활성화하고 탐지 결과를 EventBridge로 라우팅, SNS로 실시간 알림을 전달하는 탐지 파이프라인 구성.

### 아키텍처
```
GuardDuty (탐지) → EventBridge (라우팅) → SNS (알림)
```
- GuardDuty: VPC Flow Logs, DNS 쿼리 로그, CloudTrail 이벤트를 분석해 이상 징후 탐지
- EventBridge: GuardDuty Finding 이벤트를 이벤트 패턴 기반으로 필터링·라우팅
- SNS: 담당자에게 실시간 알림 발송

### 검증 내역
- GuardDuty 활성화
- Sample Findings 생성 (409건) — EventBridge 필터링 테스트용
- EventBridge Rule 생성: `source: aws.guardduty`, `detail-type: GuardDuty Finding` 패턴으로 이벤트 필터링
- SNS Topic 생성 및 이메일 구독 → GuardDuty Finding 발생 시 알림 수신 확인
- (실무 사례) PCI-DSS 증적 작업(FocusAI)에서 동일 구조로 GuardDuty → EventBridge → SNS 파이프라인 구축, 감사 대응용 증적으로 활용

### 실무 연계
PCI-DSS Requirement 10/11(실시간 이상탐지 및 알림)의 감사 증적으로 실제 고객사 환경에 적용한 경험과 동일한 아키텍처