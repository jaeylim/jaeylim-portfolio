### AWS/NCP 보안 아키텍처
AWS/NCP 환경에서 산업별 규제 요건에 맞춰 설계한 인프라 아키텍처

| 문서 | 클라우드 | 산업/규제 | 핵심 특징 |
|---|---|---|---|
| [aws-pci-dss-architecture.md](./aws-pci-dss-architecture.md) | AWS | 금융/PCI-DSS | VPC 단위 환경 분리, mTLS, CloudHSM 기반 키 관리 |
| [ncp-public-institution-architecture.md](./ncp-public-institution-architecture.md) | NCP (공공 리전) | 공공기관/망분리 | Transit VPC 경유 IPS 인라인 검사, NKS 오토스케일링 |
| [cloudformation-network-iac.md](./cloudformation-network-iac.md) | AWS | - | 기존 콘솔 구성 리소스의 CloudFormation IaC 전환 |

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


## 공통 설계 원칙

산업과 규제 요건은 다르지만, 두 아키텍처 모두 다음 원칙을 공유한다.

- **계층 분리**: Public/Private Subnet을 역할(Web/WAS/DB)별로 분리하고, 인터넷 인바운드는 반드시 WAF/보안 계층을 경유하도록 강제
- **중앙집중식 경유지를 통한 트래픽 통제**: PCI-DSS 환경은 Security VPC를 통해서만 외부 접근을 허용하고, 공공기관 환경은 Transit VPC를 공통 검사 지점으로 분리해 IPS를 여러 워크로드 VPC가 재사용하도록 구성
- **네트워크 격리**: Transit Gateway/VPC Peering으로 VPC 간 연결을 명시적으로 관리하고, 키 관리(CloudHSM)나 검사(IPS) 같은 민감 영역은 별도 VPC로 분리해 직접 라우팅을 차단

이 차이는 규제 요건에 따라 아키텍처를 다르게 설계해야 한다는 판단에서 비롯됐다 — PCI-DSS는 카드데이터 환경(CDE) 격리와 암호화 키 관리에, 공공기관 환경은 망분리와 검사 지점 중앙화에 우선순위를 뒀다.

