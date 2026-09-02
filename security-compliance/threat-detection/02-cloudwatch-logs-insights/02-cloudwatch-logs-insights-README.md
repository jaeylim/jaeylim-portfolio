### 02. CloudWatch Log Analytics (Logs Insights) 기반 로그 분석
CloudWatch Log Analytics(Logs Insights)를 활용해 로그인 실패 패턴을 탐지하는 쿼리

> 참고: CloudWatch Logs Insights는 2026년 6월 통합 콘솔 개편으로 "Log Analytics"라는 이름으로 변경됨.

### 배경
GuardDuty 파트에 이어지는 로그 분석용으로 구성. 실제 위협 로그 대신 CLI로 샘플 로그를 주입해, 반복적인 로그인 실패 → 성공 패턴(무차별 대입 공격 의심 시나리오)을 쿼리로 탐지하는 흐름을 시연했던 건을 인증 보완용으로 적용.

### 샘플
**Step 1. 샘플 로그 주입 (AWS CLI)**
`/demo/login-events` 로그 그룹에 `ConsoleLogin` 이벤트를 주입. 동일 IP에서 반복된 인증 실패 후 성공하는 패턴을 시뮬레이션:
```bash
aws logs put-log-events \
  --log-group-name /demo/login-events \
  --log-stream-name stream-1 \
  --log-events '[...]'  # eventName, sourceIPAddress, errorMessage 포함
```
**Step 2. Log Analytics 쿼리**
```
fields @timestamp, sourceIPAddress, eventName, errorMessage
| filter eventName = "ConsoleLogin" and errorMessage like /Failed/
| stats count() as failCount by sourceIPAddress
| sort failCount desc
```
특정 IP에서 인증 실패가 반복되는 패턴을 집계해, 무차별 대입(brute-force) 시도 여부를 빠르게 식별하는 쿼리.

### 실무 연계
컴플라이언스 감사(PCI-DSS Requirement 10 등)에서 요구하는 "비정상 접근 시도 탐지 및 로그 검토" 증적으로 활용 가능한 쿼리 패턴. 실제 운영 환경에서는 CloudTrail 관리 이벤트 로그 그룹을 대상으로 동일한 쿼리 구조를 적용.