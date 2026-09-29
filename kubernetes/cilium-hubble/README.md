### 네트워크 정책 및 트래픽 가시성 (Cilium / Hubble)
NCP Kubernetes Service(NKS, Kubernetes v1.36) 클러스터의 Cilium CNI 환경에서, NetworkPolicy 기반 네임스페이스 간 접근통제를 구현하고 Hubble(CLI/UI)로 통제 동작을 검증

### 위험
Kubernetes는 별도의 NetworkPolicy가 적용되지 않은 경우 모든 파드 간 통신을 허용하기 때문에 하나의 워크로드가 침해되면 클러스터 내부로 측면 이동(lateral movement)이 가능함. 또한 네임스페이스는 리소스를 논리적으로 구분하는 기능이며, 네트워크 격리를 제공하지 않음.

### 통제
- `client`, `backend`, `attacker` 네임스페이스 구성
- `backend` 파드를 대상으로 Ingress NetworkPolicy 적용 
- `client` 네임스페이스에서 유입되는 트래픽만 명시적으로 허용
- `backend` 파드가 Ingress 정책에 의해 선택되면 명시적으로 허용되지 않은 Ingress 트래픽은 거부되는 allow-list 방식으로 동작
- 별도의 차단 대상 목록을 관리하지 않아도 새롭게 생성된 네임스페이스는 허용 조건을 충족하지 않는 한 `backend로 접근할 수 없음.

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-from-client
  namespace: backend
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
    - Ingress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: client
```

### 검증
### 1. 애플리케이션 레벨 (curl)
허용된 통신 (client → backend)
```
$ kubectl exec -n client client -- curl -s -o /dev/null -w "%{http_code}\n" backend.backend.svc.cluster.local
200
```

차단된 통신 (attacker → backend)
```
$ kubectl exec -n attacker attacker -- curl -s -o /dev/null -w "%{http_code}\n" --max-time 5 backend.backend.svc.cluster.local
000
command terminated with exit code 28
```

### 2. CNI 레벨 (Hubble CLI)
허용된 트래픽 (client)
```
Sep 17 14:51:41: client/client:55950 -> backend/backend:80 to-overlay FORWARDED (TCP Flags: SYN)
Sep 17 14:51:41: client/client:55950 <- backend/backend:80 to-endpoint FORWARDED (TCP Flags: SYN, ACK)
```

차단된 트래픽 (attacker), backend 파드가 위치한 노드의 Cilium 에이전트에서 확인
```
Sep 17 15:03:26: attacker/attacker:57028 <> backend/backend:80 policy-verdict:none INGRESS DENIED (TCP Flags: SYN)
Sep 17 15:03:26: attacker/attacker:57028 <> backend/backend:80 Policy denied DROPPED (TCP Flags: SYN)
```

### 3. 시각화 (Hubble UI)
NKS의 Cilium은 NCP 관리형(Helm 외부 배포)이라 `cilium hubble enable --ui`가 `release: not found`로 실패함. 클러스터에 Hubble이 활성화되어 있음을 확인한 뒤(`cilium-config`의 `enable-hubble: true`), [NCP 공식 가이드](https://guide.ncloud-docs.com/docs/en/cilium-hubble-install-example) 기반으로 Hubble Relay/UI만 추가 배포하여 기존 Cilium 설정 변경 없이 적용

```
$ kubectl apply -f manifests/hubble.yaml
$ kubectl -n kube-system port-forward svc/hubble-ui 12000:80
```

플로우 테이블: client → backend `forwarded`, attacker → backend `dropped`
<img width="1252" height="653" alt="Screenshot 2026-09-29 at 2 41 04 PM" src="https://github.com/user-attachments/assets/e6ba13bd-0dfd-4f17-8d70-430af91a3a1b" />

### 확인된 사항
- NetworkPolicy에 정의한 Ingress 접근통제가 Cilium 데이터플레인에서 실제로 적용되는 것을 애플리케이션 레벨(curl)과 네트워크 관측 레벨(Hubble policy verdict)에서 교차 검증
- Hubble 플로우는 노드별 Cilium 에이전트 단위로 기록되며, 최종 정책 판정(DENIED/DROPPED)은 목적지 파드가 위치한 노드의 에이전트에서 확인됨
- 동일 연결이 출발지 egress 지점에서는 `forwarded`, 목적지 ingress 지점에서는 `dropped`로 관측됨. 차단은 목적지 ingress에서 발생하며 출발지 측 기록은 정책 우회가 아님
- 관리형 Kubernetes에서는 CNI의 설치·업그레이드·설정 주체가 클라우드 사업자일 수 있으므로, CNI 기능 확장이나 운영 방식 변경 시 업스트림 문서와 함께 클라우드 사업자의 지원 범위 및 공식 가이드를 확인할 필요가 있음
