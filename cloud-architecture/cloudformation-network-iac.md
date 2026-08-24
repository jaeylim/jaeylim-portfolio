### 기존 AWS 리소스의 CloudFormation IaC 전환
기존 콘솔에서 수동으로 구축되어 있던 AWS 네트워크 리소스를 CloudFormation으로 역추출하여 IaC 관리 체계로 변경

### 전환 배경
인프라가 이미 운영 중인 상태에서, 향후 변경 관리와 재현성을 위해 콘솔로 구성된 리소스를 IaC로 전환할 필요 존재. 
AWS CloudFormation IaC Generator를 사용해 기존 리소스를 스캔하고 템플릿으로 추출하는 과정으로 진행.

VPC 도메인별로 스택을 분리하여 관리 (EX.DEV/PRD/SEC/HSM, etc.)

### PP VPC 네트워크 구성
- VPC: `10.2.0.0/16`
- 서브넷 구성 (2개 AZ, 총 10개 서브넷)

| 용도 | AZ-A | AZ-C |
|---|---|---|
| Public | 10.2.0.0/24 | 10.2.1.0/24 |
| Private-Web | 10.2.2.0/24 | 10.2.3.0/24 |
| Private-WAS | 10.2.4.0/24 | 10.2.5.0/24 |
| Private-DB | 10.2.6.0/24 | 10.2.7.0/24 |
| Private-TS | 10.2.8.0/24 | 10.2.9.0/24 |

- IGW, NAT Gateway(고정 EIP) 구성
- Route Table: Public(IGW 경유) / Private(NAT + Transit Gateway 경유) 분리
- Transit Gateway를 통해 사내 다른 네트워크 대역(10.0.2.0/24, 10.1.2.0/24, 10.1.3.0/24)과 연결

### 스택 분리와 Export/Import
VPC/Route/NACL을 개별 스택으로 분리하고, `Fn::ImportValue`로 스택 간 리소스를 참조하도록 구성. 
VPC 스택에서 서브넷·IGW·NAT ID 등을 `Export`하면, Route/NACL 스택이 이를 `Fn::ImportValue`로 가져와 사용하는 구조가 됨. 
이렇게 하면 스택별로 독립적인 업데이트/배포가 가능.

### 리비전 관리
VPC 스택은 최초 버전에서 `EnableDnsHostnames: true`로 생성했으나, 이후 `false`로 수정한 버전을 실제 배포에 반영했다.

### 재현 방법
CloudFormation 콘솔 또는 CLI에서 스택 순서대로 배포 (VPC → Route/NACL 순, Export 값 의존성 때문).

```bash
aws cloudformation deploy --template-file prd-vpc-stack.json --stack-name prd-vpc-stack
aws cloudformation deploy --template-file prd-route-stack.json --stack-name prd-route-stack
aws cloudformation deploy --template-file prd-nacl-stack.json --stack-name prd-nacl-stack
```

※ 실제 고객사 정보는 일반화하여 기술하였습니다.