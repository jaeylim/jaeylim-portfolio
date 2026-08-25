### AWS CloudHSM 기반 KMS Custom Key Store 구성
PCI-DSS 요구사항(키 관리, HSM 기반 암호화) 충족을 위해 AWS KMS와 CloudHSM을 연동하여
custom key store를 구성하고, 운영/개발 환경에 맞는 클러스터 아키텍처를 설계·검증

### 1. 배경 — 왜 KMS 단독이 아니라 CloudHSM인가
PCI-DSS 등 규제 준수 환경에서는 암호화 키 관리 방식이 감사 대상이 됩니다. AWS KMS는 편리하지만
키 자재(key material)가 AWS 소유·관리 인프라 내부 소프트웨어 계층에 존재합니다. 반면 CloudHSM은
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
  중간 클라이언트 서버라는 관리 포인트를 제거했.
- Transit Gateway로 연결된 VPC라면 사설 통신 경로만 확보되면 어느 VPC의 리소스에서도
  HSM 클러스터에 접근 가능하다는 점을 검증.

### 3. 클러스터 vs 단일 HSM
| 구분 | 운영(prod) | 개발(dev) |
|---|---|---|
| HSM 구성 | 클러스터 (AZ-a + AZ-c, 2대) | 단일 (AZ-a, 1대) |
| 이유 | 고가용성(HA) 필요 | 시간당 과금되는 HSM 비용을 개발 환경까지 이중화할 필요 없음 |

- KMS custom key store에서 `kmsuser`를 crypto-user로 연결하는 순간,
HSM이 자동으로 최소 2개 가용영역에 걸쳐 있어야 한다는 KMS 측 제약이 있습니다
(`CloudHsmClusterInvalidConfigurationException: CloudHSM cluster must contain active HSMs
in at least two Availability Zones`). 이 제약이 곧 "운영 환경은 자연스럽게 HA 클러스터가
강제된다"는 설계 근거가 되었고, 반대로 개발 환경은 KMS 연동 없이 단일 HSM으로 비용을 절감했습니다.

### 4. KMS Custom Key Store 연동
공식 가이드(Create a custom key store)를 따라가면 아래 순서로 끝나는 것처럼 보입니다.

1. CloudHSM 클러스터 생성 및 초기화(CSR 서명, 인증서 업로드)
2. 클러스터 activate
3. `kmsuser` 생성 (`user create --username kmsuser --role crypto-user`)
4. KMS 콘솔에서 custom key store 생성 (클러스터 선택, anchor certificate 업로드, kmsuser 인증)
5. Key store `connect`

**하지만 여기까지는 "KMS가 HSM을 백엔드로 쓸 수 있도록 연결"한 것일 뿐, 실제로 암복호화에
사용할 키는 아직 존재하지 않습니다.** custom key store 연결(인프라 레벨)과 CMK 생성(키 레벨)은
분리된 별개의 단계이며, 이 부분이 공식 가이드 흐름만 따라가면 누락되기 쉬운 지점입니다.

이 프로젝트에서는 custom key store를 origin으로 지정해 **CMK를 별도 생성**하고, 키 정책(key
policy)에서 관리자 권한과 사용자(암복호화) 권한을 분리해 PCI-DSS의 직무 분리(separation of
duties) 요구사항을 반영했습니다.

> KMS와 CloudHSM의 역할 관계를 정리하면: KMS는 API 요청을 받아 IAM 정책·키 정책을 검증하고
> CloudTrail에 로깅하는 **컨트롤 플레인**이며, 실제 암호화 연산과 키 자재 보관은 뒤에서
> CloudHSM에 위임하는 구조입니다. 즉 "키가 어디 물리적으로 존재하는가(HSM)"와
> "누가 그 키를 어떻게 쓸 수 있는가(KMS)"가 계층적으로 분리되어 있습니다.

### 5. 트러블슈팅 — Multi-Cluster 연결 실패
[증상] 하나의 CloudHSM 클라이언트 서버(hsm-client)에서 서로 다른 두 클러스터(예: 운영 클러스터 +
별도 조직/계정의 클러스터)를 동시에 연결하려고 `configure-cli add-cluster` 명령을 실행했으나
아래 에러로 반복 실패:
```
DescribeClusters call failed with error: CommonApiError(InternalError("dispatch failure")).
Retrying the call.
'dispatch failure'
```

[시도한 방법]
| 시도 | 방법 | 결과 |
|---|---|---|
| 1 | 기존 cfg 파일 유지한 채 `add-cluster --cluster-id ... --hsm-ca-cert ...` 실행 | `dispatch failure` 반복 |
| 2 | 두 번째 클러스터 전용 별도 cfg 파일 생성 후 `interactive --config <파일>` 옵션으로 분리 실행 | cloudhsm-cli가 `--config`, `--cluster-id` 옵션을 지원하는 것은 확인, 검증 계속 진행 중 |
| 3 (실패) | 기존 cfg 삭제 후 `-a <HSM IP>`와 `--cluster-id`를 함께 사용 | `-a` 옵션과 `--cluster-id` 옵션은 상호 배타적이라는 에러로 실패 |

결론 및 실무 판단: 공식 문서상 `add-cluster` 기능 자체는 존재하지만, 실제 환경에서는
API 레벨 오류가 재현되어 즉시 안정화되지 않았습니다. 이런 상태에서 검증되지 않은 CLI
명령어를 그대로 고객 환경에 전달하는 것은 리스크가 있다고 판단하여, **클라이언트 서버당
단일 클러스터 연결을 기본 구성으로 유지**하고 멀티 클러스터 연결은 별도 검증 과제로 분리
기록했습니다. (엔지니어링 판단: "된다고 알려진 기능"과 "지금 이 환경에서 안정적으로 되는
기능"을 구분해서 고객에게 전달해야 한다는 원칙 적용)

### References
- [AWS CloudHSM User Guide — Use Cases](https://docs.aws.amazon.com/cloudhsm/latest/userguide/use-cases.html)
- [AWS KMS — Create a custom key store](https://docs.aws.amazon.com/kms/latest/developerguide/create-keystore.html)
- [AWS CloudHSM CLI Reference](https://docs.aws.amazon.com/cloudhsm/latest/userguide/cloudhsm_cli-reference.html)
- [AWS CloudHSM — Multi-cluster CLI](https://docs.aws.amazon.com/cloudhsm/latest/userguide/cloudhsm_cli-multi-cluster-add-cluster.html)