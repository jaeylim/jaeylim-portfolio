### tooling/settings.md
Zammad 애플리케이션 레벨 설정 기록 (Entra ID SSO 연동, Core Workflows 트리거, 커스텀 State)

### 1. Entra ID SSO 연동

### 1.1 Entra ID 앱 등록

### 1.2 Zammad 측 SSO 설정
- (관리자 콘솔 → System → Security → 3rd Party Applications 경로 등)

### 1.3 연동 확인
- (테스트 로그인 스크린샷/결과)


### 2. Core Workflows 트리거 설정

### 2.1 트리거 목록
| 트리거명 | 조건 | 액션 |
|---|---|---|
| (예: 결재자 알림) | 티켓 접수 시 | 결재자에게 알림 발송 |
| | | |

### 2.2 승인/반려 분기 설정
- (UI 스크린샷 또는 조건 로직 기록)

### 2.3 상태별 알림 설정
- (진행중/종료 알림 트리거 상세)


### 3. 커스텀 State 적용 확인
- 4.2(README.md)에서 Rails 서버에 직접 추가한 `In progress` State가 실제 UI에 반영되었는지 확인
- (Admin → Ticket → States 화면 스크린샷 등)

### 4. 검증 / 테스트 기록
- (실제 티켓 접수 → 결재 → 승인/반려 → 종료까지 End-to-End 테스트 결과)