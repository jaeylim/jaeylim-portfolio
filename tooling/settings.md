Zammad 애플리케이션 레벨 설정
(Entra ID SSO 연동, Core Workflows 트리거, 커스텀 State)

### 1. Entra ID SSO 연동
### 1.1 Entra ID 앱 등록
[Settings] - [Security] - [Third-party Applications : Authentication via Microsoft]
APP ID: 
APP SECRET: 
APP TENANT ID: 

### 1.2 Zammad 측 SSO 설정
- (관리자 콘솔 → System → Security → 3rd Party Applications 경로 등)

### 2. Core Workflows 트리거 설정
### 2.1 트리거 목록
(예시) 결재자 알림
![alt text]("C:\Users\jaeyeonlim\Downloads\image-20260807-070640.png")

- 결재자 알림
- 담당자 알림(반려)
- 담당자 알림(승인)
- 담당자 알림(진행중)
- 티켓 접수 이후 알림
- 티켓 종료 이후 알림
