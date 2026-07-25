### AWS/NCP 보안 아키텍처

PCI-DSS 요구사항을 기준으로 AWS 인프라 보안 구성을 설계·구축·운영한 기록.

#### 네트워크·접근 통제

- Security Group 점검: 불필요한 인바운드 규칙(0.0.0.0/0 오픈 등) 확인 및 제거
- IAM Password Policy 구성: 12자 이상, 대소문자·숫자·특수문자 포함, 90일 만료, 재사용 방지
- IAM Policy 점검: Action/Resource 와일드카드 사용 여부 확인, 최소 권한 원칙 적용
- Network Firewall Logging + CloudWatch Alarm 임계치 설정

#### 탐지·모니터링

- GuardDuty → EventBridge → SNS 파이프라인 구성: EventBridge Rule에서 GuardDuty를 이벤트 소스로 지정하고 SNS Target 연결, 콘솔에서 동작 확인
- Security Hub 기반 CIS Benchmark 점검

#### 통신 구간 보안

- ACM Private CA(Test Provisioning CA)에서 mTLS 클라이언트 인증서 발급
- 초기 RSA 2048로 발급 시도 실패 → CA가 ECDSA(EC_prime256v1) 기반임을 확인 후 ECDSA P256으로 재발급하여 해결
- 발급된 인증서(cert/private_key/chain)를 PKCS#12(.p12)로 변환하여 전달
- ALB Trust Store 연동

#### 트래픽 흐름 (구성 확인 기준)

```
Route53 → WAF → ALB(mTLS) → EC2
                ↑
         CloudFront (CRL 배포용)
```
