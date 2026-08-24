### AWS/NCP 보안 아키텍처
AWS/NCP 환경에서 산업별 규제 요건에 맞춰 설계한 인프라 아키텍처

| 문서 | 클라우드 | 산업/규제 | 핵심 특징 |
|---|---|---|---|
| [aws-pci-dss-architecture.md](./aws-pci-dss-architecture.md) | AWS | 금융/PCI-DSS | VPC 단위 환경 분리, mTLS, CloudHSM 기반 키 관리 |
| [ncp-public-institution-architecture.md](./ncp-public-institution-architecture.md) | NCP (공공 리전) | 공공기관/망분리 | Transit VPC 경유 IPS 인라인 검사, NKS 오토스케일링 |
| [cloudformation-network-iac.md](./cloudformation-network-iac.md) | AWS | - | 기존 콘솔 구성 리소스의 CloudFormation IaC 전환 |

### 공통 설계 원칙
산업과 규제 요건은 다르지만, 두 아키텍처 모두 다음 원칙을 공유.

- 계층 분리: Public/Private Subnet을 역할(Web/WAS/DB)별로 분리하고, 인터넷 인바운드는 반드시 WAF/보안 계층을 경유하도록 강제
- 중앙집중식 경유지를 통한 트래픽 통제: PCI-DSS 환경은 Security VPC를 통해서만 외부 접근을 허용하고, 공공기관 환경은 Transit VPC를 공통 검사 지점으로 분리해 IPS를 여러 워크로드 VPC가 재사용하도록 구성
- 네트워크 격리: Transit Gateway/VPC Peering으로 VPC 간 연결을 명시적으로 관리하고, 키 관리(CloudHSM)나 검사(IPS) 같은 민감 영역은 별도 VPC로 분리해 직접 라우팅을 차단

