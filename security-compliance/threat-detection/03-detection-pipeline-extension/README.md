### GuardDuty 기반 위협 탐지 파이프라인
GuardDuty 탐지 결과를 EventBridge로 라우팅하고 SNS로 알림을 발송하는 실시간 위협 탐지 파이프라인을 구성

### 아키텍처
```
GuardDuty (탐지) → EventBridge (라우팅) → SNS (알림)
```
- GuardDuty: VPC Flow Logs, DNS 로그, CloudTrail 이벤트 기반 위협 탐지
- EventBridge: GuardDuty Finding 이벤트를 규칙 기반으로 필터링·라우팅
- SNS: 담당자에게 실시간 알림 발송

### 운영 및 점검 항목
PCI-DSS 증적 수집 대상으로 다음을 정기 점검한다.

- Security Group 최소 권한 여부
- IAM Password Policy 설정값
- IAM Policy JSON 내 Action/Resource 범위
- Network Firewall Logging 및 CloudWatch Alarm 설정
- GuardDuty → EventBridge → SNS 알림 흐름 동작 확인

### 관련 컴플라이언스 대응
- PCI-DSS: 위 항목들을 직접 점검·캡처하여 증적으로 관리
- ISO 27001:2022 갱신 심사: 내부 보안팀과 협업하여 갱신 심사 증적 자료 준비, 2013판 → 2022판 통제 항목 변경 사항 매핑
- CSAP 사후평가: 연 1회 서면평가 체계 대응, SaaS 표준형 인증 서비스 별첨3 등 제출 자료 준비, 개발/운영 담당자와 증적 수집 범위 조율
- 개인정보보호법 개정 대응: 2026년 개정사항(CPO 지정, 유출 통지, 과징금 등) 반영하여 내부 정책 문서 갱신, ISO 27001:2022 통제 항목과 매핑