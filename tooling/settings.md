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

<img width="500" height="429" alt="image-20260807-070640" src="https://github.com/user-attachments/assets/a1fcc064-0157-4ab4-b610-2d5b813b8072" />/n
<img width="500" height="647" alt="image-20260807-070733" src="https://github.com/user-attachments/assets/f9731106-f3fa-43da-9c01-b958b7ffd894" />

- 결재자 알림
- 담당자 알림(반려)
- 담당자 알림(승인)
- 담당자 알림(진행중)
- 티켓 접수 이후 알림
- 티켓 종료 이후 알림
