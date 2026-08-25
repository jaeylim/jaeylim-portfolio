### AWS CloudHSM 기반 KMS Custom Key Store 구성
PCI-DSS 요구사항(키 관리, HSM 기반 암호화) 충족을 위해 AWS KMS와 CloudHSM을 연동하여
custom key store를 구성하고, 운영/개발 환경에 맞는 클러스터 아키텍처를 설계·검증

### 1. 배경
PCI-DSS 등 규제 준수 환경에서는 암호화 키 관리 방식이 감사 대상이 됨. 
AWS KMS는 키 자재(key material)가 AWS 관리 인프라 내부 소프트웨어 계층에 존재하지만, CloudHSM은
전용 하드웨어 장치(FIPS 140-2 Level 3 인증)를 통해 물리적으로 격리된 환경에서 키를  생성·보관하며, 난수 생성 방식부터 다릅니다(HSM은 H/W noise 기반, 일반 서버는 S/W 알고리즘 기반).

### 2. 아키텍처
```
                    [Transit Gateway]
                           │
                ┌──────────┴──────────┐
                │                     │
        [WAS VPC / App]        [CloudHSM VPC]
        PKCS#11 라이브러리      ┌─────────────────────────┐
        설치된 WAS 서버   ────▶ │  AZ-a          AZ-c      │
        (HSM 직접 접근)        │  ┌─────────┐  ┌─────────┐│
                               │  │prod-HSM │  │prod-HSM ││  ← 클러스터(HA)
                               │  │dev-HSM  │  │         ││  ← dev는 단일
                               │  └─────────┘  └─────────┘│
                               └─────────────────────────┘
```
- 초기에는 별도 클라이언트 서버를 두고 거기서 HSM에 접속하는 구조였으나,
  이후 WAS(PKCS#11 라이브러리 탑재)가 HSM에 직접 접근하도록 아키텍처를 단순화하여
  중간 클라이언트 서버라는 관리 포인트 제거.
- Transit Gateway로 연결된 VPC라면 사설 통신 경로만 확보되면 어느 VPC의 리소스에서도
  HSM 클러스터에 접근 가능.

### 3. 클러스터 vs 단일 HSM
| 구분 | 운영(prod) | 개발(dev) |
|---|---|---|
| HSM 구성 | 클러스터 (AZ-a + AZ-c, 2대) | 단일 (AZ-a, 1대) |
| 이유 | 고가용성(HA) 필요 | 시간당 과금되는 HSM 비용을 개발 환경까지 이중화할 필요 없음 |

- KMS custom key store에서 `kmsuser`를 crypto-user로 연결하게되면, HSM이 자동으로 최소 2개 가용영역에 걸쳐 있어야 한다는 제약 (`CloudHsmClusterInvalidConfigurationException: CloudHSM cluster must contain active HSMs in at least two Availability Zones`) 있음. 이 제약 때문에 "운영 환경은 자연스럽게 HA 클러스터가 강제된다"는 설계 근거가 되었고, 반대로 개발 환경은 KMS 연동 없이 단일 HSM으로 비용 절감.

### 4. KMS 연동

1. CloudHSM 클러스터 생성 및 초기화(CSR 서명, 인증서 업로드)
2. 클러스터 activate
3. `kmsuser` 생성 (`user create --username kmsuser --role crypto-user`)
4. KMS 콘솔에서 custom key store 생성 (클러스터 선택, anchor certificate 업로드, kmsuser 인증)
5. Key store `connect`

이 단계까지 하면 KMS가 HSM을 백엔드로 연결한 것 뿐 실제 암복호화에 사용될 키는 생성되지 않은 상태이기 때문에 "custom key store 연결(인프라 레벨)"과 "Customer managed keys 생성(키 레벨)"을 각각 진행해야 함. 

1. custom key store를 origin으로 지정해서 Customer managed keys(CMK) 별도 생성

> KMS와 CloudHSM의 역할 관계를 정리하면: KMS는 API 요청을 받아 IAM 정책·키 정책을 검증하고
> CloudTrail에 로깅하는 **컨트롤 플레인**이며, 실제 암호화 연산과 키 자재 보관은 뒤에서
> CloudHSM에 위임하는 구조입니다. 즉 "키가 어디 물리적으로 존재하는가(HSM)"와
> "누가 그 키를 어떻게 쓸 수 있는가(KMS)"가 계층적으로 분리되어 있습니다.

### References
- [AWS CloudHSM User Guide — Use Cases](https://docs.aws.amazon.com/cloudhsm/latest/userguide/use-cases.html)
- [AWS KMS — Create a custom key store](https://docs.aws.amazon.com/kms/latest/developerguide/create-keystore.html)
- [AWS CloudHSM CLI Reference](https://docs.aws.amazon.com/cloudhsm/latest/userguide/cloudhsm_cli-reference.html)
- [AWS CloudHSM — Multi-cluster CLI](https://docs.aws.amazon.com/cloudhsm/latest/userguide/cloudhsm_cli-multi-cluster-add-cluster.html)