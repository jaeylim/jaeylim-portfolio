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

<img width="500" height="429" alt="image-20260807-070640" src="https://github.com/user-attachments/assets/a1fcc064-0157-4ab4-b610-2d5b813b8072" />
<br/>
<img width="500" height="647" alt="image-20260807-070733" src="https://github.com/user-attachments/assets/f9731106-f3fa-43da-9c01-b958b7ffd894" />

- 결재자 알림
- 담당자 알림(반려)
- 담당자 알림(승인)
- 담당자 알림(진행중)
- 티켓 접수 이후 알림
- 티켓 종료 이후 알림

[결재자 알림]
[CONDITIONS FOR AFFECTED OBJECTS] 
1) State - is - new
2) Action - is - created

[EXECUTE CHANGES ON OBJECTS] 
1) Email
2) SUBJECT: [결재알림] 승인 요청 #{ticket.title}
3) BODY: 
```text
🔐 보안 요청 티켓이 접수되었습니다.
담당자 확인 및 승인이 필요합니다.
아래 링크에서 티켓 내용을 검토해 주세요.
티켓 링크: #{config.http_type}://#{config.fqdn}/#ticket/zoom/#{ticket.id}
담당자 알림(반려)
```
[CONDITIONS FOR AFFECTED OBJECTS] 
1) State - is - rejected
[EXECUTE CHANGES ON OBJECTS] 
1) Email
2) SUBJECT: [반려] 티켓이 반려되었습니다 - #{ticket.title}
3) BODY: 
```text
❌ 보안 요청이 반려되었습니다.
요청 내용을 검토 후 티켓을 다시 접수해 주세요.
#{article.body}
▶ 신규 티켓 접수
#{config.http_type}://#{config.fqdn}
담당자 알림(승인)
```

[CONDITIONS FOR AFFECTED OBJECTS] 
1) State - is - approved
[EXECUTE CHANGES ON OBJECTS] 
1) Email
2) SUBJECT: [승인완료] 담당자 할당 #{ticket.title}
3) BODY: 
```text
✅ 보안 요청이 승인되었습니다.
담당자가 배정되었으니 아래 링크에서 티켓을 확인해 주세요.
▶ 티켓 바로가기
#{config.http_type}://#{config.fqdn}/#ticket/zoom/#{ticket.id}
담당자 알림(진행중)
```

[CONDITIONS FOR AFFECTED OBJECTS] 
1) State - is - In progress
2) Action - is - updated
[EXECUTE CHANGES ON OBJECTS] 
1) Email
2) SUBJECT: [진행중] 티켓이 진행중입니다 - #{ticket.title}
3) BODY: 
```text
👩‍💻티켓을 처리중입니다.
▶ 티켓 커멘트
#{article.body}
▶ 티켓 바로가기
#{config.http_type}://#{config.fqdn}/#ticket/zoom/#{ticket.id}
티켓 접수 이후 알림
```

[CONDITIONS FOR AFFECTED OBJECTS] 
1) Action - is - created
2) State - is not -closed
3) Type - is - web
4) Sender - is -Customer
[EXECUTE CHANGES ON OBJECTS] 
1) Email
2) SUBJECT: 문의 접수 완료 (#{ticket.title})
3) BODY: 
```text
안녕하세요,
문의하신 요청(#{config.ticket_hook}#{ticket.number})이 정상적으로 접수되었습니다.
결재자 검토 후 순차적으로 처리해 드리겠습니다.
추가 정보 제공이 필요하신 경우, 본 메일에 회신하시거나 아래 링크를 통해 티켓을 확인하실 수 있습니다. (최초 로그인 시 비밀번호 재설정이 필요합니다)
#{config.http_type}://#{config.fqdn}/#ticket/zoom/#{ticket.id}
감사합니다.
#{config.product_name} 보안팀
티켓 종료 이후 알림
```

[CONDITIONS FOR AFFECTED OBJECTS] 
1) State - is - closed
[EXECUTE CHANGES ON OBJECTS] 
1) Email
2) SUBJECT: [처리완료] 보안 요청 사항 처리 완료 - #{ticket.title}
3) BODY: 
```text
👩‍💻 티켓이 처리되었습니다.
추가 요청 사항은 신규 티켓으로 접수 부탁드립니다.
▶ 신규 티켓 접수
#{config.http_type}://#{config.fqdn}
```