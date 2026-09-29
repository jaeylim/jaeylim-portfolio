### Admission Control / Policy as Code (Kyverno)
NCP Kubernetes Service(NKS, Kubernetes v1.36) 클러스터에 Kyverno를 설치하고, 컨테이너 보안 기준을 정책 코드로 정의해 배포 단계에서 위반 워크로드를 차단

### 위험
Kubernetes는 기본적으로 파드 스펙의 보안 설정을 검증하지 않아, 다음과 같은 워크로드가 그대로 배포될 수 있음

- **privileged 컨테이너**: 호스트 커널·디바이스에 직접 접근 가능 → 컨테이너 탈출 시 노드 장악
- **root 실행 컨테이너**: 취약점 악용 시 컨테이너 내부 최고 권한 획득, 탈출 시 피해 확대
- **출처 불명 이미지**: 검증되지 않은 퍼블릭 레지스트리 이미지로 인한 공급망 위험

보안 기준이 문서로만 존재하면 준수 여부가 배포자 개인에게 의존하게 됨

### 통제
Kyverno admission webhook으로 파드 생성 요청을 API 서버 단계에서 검사하고, 정책 위반 시 거부(`Enforce`)

| 정책 | 통제 내용 |
|---|---|
| `disallow-privileged-containers` | `privileged: true` 컨테이너 차단 |
| `require-run-as-nonroot` | `runAsNonRoot: true` 명시 필수 (파드 또는 컨테이너 레벨) |
| `restrict-image-registries` | 허용 레지스트리(`ghcr.io/jaeylim/*`, `nginxinc/*`) 외 이미지 차단 |

### 설계 시 고려사항
- **적용 범위 통제**: 공유 클러스터 환경이므로 정책을 `kyverno-test` 네임스페이스로 한정. 클러스터 전역 Enforce 적용 시 기존 워크로드 배포까지 차단될 수 있음
- **오탐 방지**: 필드가 없으면 통과하는 조건부 앵커 `=()`와 필수 명시(앵커 없음)를 구분해 작성. 예) privileged는 미지정 시 기본값이 false이므로 `=(privileged)`로 "지정된 경우에만" 검사하고, runAsNonRoot는 명시를 강제
- **fail-closed**: Kyverno admission webhook의 failurePolicy 기본값이 Fail이므로, Kyverno가 요청을 정상처리하지 못할 경우 API 요청을 거부. 보안상 안전한 기본값이지만 Kyverno 장애가 배포 장애로 이어질 수 있는 트레이드오프가 있기 때문에 시스템 네임스페이스(`kube-system`, `kyverno`)는 기본 제외됨.

<details>
<summary>정책 코드</summary>

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: disallow-privileged-containers
spec:
  validationFailureAction: Enforce
  background: true
  rules:
  - name: privileged-containers
    match:
      any:
      - resources:
          kinds: [Pod]
          namespaces: [kyverno-test]
    validate:
      message: "Privileged 컨테이너는 허용되지 않습니다."
      pattern:
        spec:
          =(initContainers):
          - =(securityContext):
              =(privileged): "false"
          containers:
          - =(securityContext):
              =(privileged): "false"
```

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-run-as-nonroot
spec:
  validationFailureAction: Enforce
  background: true
  rules:
  - name: run-as-non-root
    match:
      any:
      - resources:
          kinds: [Pod]
          namespaces: [kyverno-test]
    validate:
      message: "runAsNonRoot: true 설정이 필요합니다 (root 실행 금지)."
      anyPattern:
      - spec:
          securityContext:
            runAsNonRoot: true
          =(initContainers):
          - =(securityContext):
              =(runAsNonRoot): true
          containers:
          - =(securityContext):
              =(runAsNonRoot): true
      - spec:
          =(initContainers):
          - securityContext:
              runAsNonRoot: true
          containers:
          - securityContext:
              runAsNonRoot: true
```

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: restrict-image-registries
spec:
  validationFailureAction: Enforce
  background: true
  rules:
  - name: allowed-registries
    match:
      any:
      - resources:
          kinds: [Pod]
          namespaces: [kyverno-test]
    validate:
      message: "허용된 레지스트리(ghcr.io/jaeylim, nginxinc)의 이미지만 사용할 수 있습니다."
      pattern:
        spec:
          =(initContainers):
          - image: "ghcr.io/jaeylim/* | nginxinc/*"
          containers:
          - image: "ghcr.io/jaeylim/* | nginxinc/*"
```

</details>

### 검증
각 테스트 파드가 정책 하나씩만 위반하도록 구성해, 차단 사유가 정책별로 분리되어 확인되도록 설계

| 테스트 파드 | 위반 항목 | 기대 결과 |
|---|---|---|
| `bad-privileged` | privileged: true | 차단 |
| `bad-root` | runAsNonRoot 미지정 | 차단 |
| `bad-registry` | `nginx:1.27` (허용 외 레지스트리) | 차단 |
| `good-pod` | 없음 | 생성 |

### 1. 정책 적용 상태
```
$ kubectl get clusterpolicy
```

### 2. 위반 파드 차단
```
$ kubectl apply -f test-pods.yaml
pod/good-pod created

resource Pod/kyverno-test/bad-privileged was blocked due to the following policies
disallow-privileged-containers:
  privileged-containers: 'validation error: Privileged 컨테이너는 허용되지 않습니다.
  rule privileged-containers failed at path /spec/containers/0/securityContext/privileged/'

resource Pod/kyverno-test/bad-root was blocked due to the following policies
require-run-as-nonroot:
  run-as-non-root: 'validation error: runAsNonRoot: true 설정이 필요합니다 (root 실행 금지).
  rule run-as-non-root[0] failed at path /spec/securityContext/runAsNonRoot/
  rule run-as-non-root[1] failed at path /spec/containers/0/securityContext/'

resource Pod/kyverno-test/bad-registry was blocked due to the following policies
restrict-image-registries:
  allowed-registries: 'validation error: 허용된 레지스트리(ghcr.io/jaeylim, nginxinc)의 이미지만 사용할 수 있습니다.
  rule allowed-registries failed at path /spec/containers/0/image/'
```

### 3. 정상 파드만 생성
```
$ kubectl get pod -n kyverno-test
NAME       READY   STATUS    RESTARTS   AGE
good-pod   1/1     Running   0          22s
```
```
$ kubectl get clusterpolicy
NAME                             ADMISSION   BACKGROUND   READY   AGE   MESSAGE
disallow-privileged-containers   true        true         True    8h    Ready
require-run-as-nonroot           true        true         True    8h    Ready
restrict-image-registries        true        true         True    8h    Ready
```

### 확인된 사항
- 정책 위반 시 차단 메시지에 위반 정책명과 필드 경로(`/spec/containers/0/...`)가 함께 기록되어, 배포자가 수정 지점을 즉시 파악 가능
- `anyPattern`은 하위 패턴 중 하나만 충족하면 통과하며, 모두 실패한 경우 각 패턴의 실패 경로(`[0]`, `[1]`)가 개별 출력됨
- Kyverno 1.19(Helm chart 3.9.1)가 공식 테스트 범위(K8S 1.33~1.35) 밖인 NKS 1.36 환경에서 정상 동작함을 확인
- 본 실습은 레거시 `ClusterPolicy`의 pattern 기반 정책으로 작성. Kyverno 1.19에서 ClusterPolicy/Policy API가 deprecated되고 CEL 기반 `ValidatingPolicy`로 전환 중임을 확인했으며, 이는 K8S의 `ValidatingAdmissionPolicy` CEL 기반 정책 체계와 정렬되는 방향.