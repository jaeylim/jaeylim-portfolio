### Service Mesh / mTLS / 접근통제 (Istio Ambient Mode)
NCP Kubernetes Service(NKS, Kubernetes v1.36) 클러스터에 Istio Ambient Mode(1.31)를 설치하고, STRICT mTLS와 신원 기반 AuthorizationPolicy로 서비스 간 인증·인가를 단계별로 검증

### 위험
클러스터 내부(east-west) 트래픽은 기본적으로 평문으로 전송되며, 네트워크 위치(IP·네임스페이스) 기반 통제만으로는 요청 주체의 신원을 확인할 수 없음. 내부 워크로드가 침해되거나 위치 정보가 신뢰할 수 없는 상황에서는 정상 요청과 비인가 요청을 구분할 근거가 없음

### 통제
| 단계 | 통제 | 목적 |
|---|---|---|
| 1 | Ambient 메시 편입 (`istio.io/dataplane-mode=ambient`) | 파드 재시작·애플리케이션 수정 없이 노드 레벨(ztunnel)에서 mTLS 적용 |
| 2 | `PeerAuthentication` STRICT | mTLS가 아닌 평문/bypass 요청 거부 →  **인증** 인증된 메시 트래픽만 허용 |
| 3 | `AuthorizationPolicy` (principals 기반 ALLOW) | 인증된 워크로드 중 허용된 신원만 접근 → **인가** |

```yaml
apiVersion: security.istio.io/v1
kind: PeerAuthentication
metadata:
  name: strict-mtls
  namespace: backend
spec:
  mtls:
    mode: STRICT
```

```yaml
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: allow-client-only
  namespace: backend
spec:
  selector:
    matchLabels:
      app: backend
  action: ALLOW
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/client/sa/default"]
```

### 설치 및 트러블슈팅
NKS의 관리형 Cilium CNI 환경에서 Ambient 설치 시 두 가지 호환성 이슈를 로그 기반으로 추적·해결

### 1. cilium `cni-exclusive` 충돌

- 증상: `istio-cni-node` 전 노드 `0/1` 상태 지속, `istioctl install` 시 `detected Cilium CNI with 'cni-exclusive=true'` 경고
- 원인: cilium이 노드의 `/etc/cni/net.d`에서 다른 CNI 설정 파일을 제거하도록 설정되어 Istio CNI 체이닝 불가
- 조치: `cilium-config`의 `cni-exclusive`를 `false`로 변경 후 Cilium DaemonSet 재시작
- 사전 확인: Istio 공식 Cilium 요건에 따라 BPF masquerading 비활성(iptables masquerade 사용), kube-proxy replacement 환경의 `bpf-lb-sock-hostns-only: true` 설정 확인. `cilium-config`가 `addonmanager.kubernetes.io/mode: EnsureExists`로 관리되어 변경값이 벤더 측에서 덮어써지지 않음을 확인

### 2. IPv4 전용 노드의 IPv6 처리 실패
- 증상 ①: `ztunnel` 전 노드 CrashLoopBackOff
```
  Error: readiness server starts
  Caused by: Address family not supported by protocol (os error 97)
```
- 증상 ②: 네임스페이스 라벨 적용 후에도 워크로드가 메시에 편입되지 않음 (`PROTOCOL: TCP`)
```
  error cni-agent failed to add route ({... Dst: ::/0 ...}): operation not supported
  error cni-agent Failed capturing pod, will not retry.
```
- 원인: NKS 노드는 커널 레벨에서 IPv6가 비활성화되어 있으나, ztunnel(서버 바인딩)과 istio-cni(파드 라우트 설치)가 기본적으로 IPv6를 사용
- 조치: 설치 설정에 IPv6 비활성화 반영 후 istio-cni 재시작, 편입 재시도를 위해 네임스페이스 라벨 재적용
```
  istioctl install --set profile=ambient \
    --set values.ztunnel.env.IPV6_ENABLED=false \
    --set values.cni.ambient.ipv6=false
```

### 검증
테스트 구성: `client`(허용 대상), `backend`(보호 대상), `attacker`(비인가 대상) 네임스페이스. Istio 통제만 단독으로 검증하기 위해 Cilium NetworkPolicy는 제거한 상태에서 진행

### 1. 메시 편입 확인
client·backend는 HBONE(mTLS 터널), 메시 밖 attacker는 TCP(평문)로 처리

```
$ istioctl ztunnel-config workloads | grep -E "client|backend|attacker"
attacker     attacker                                       198.18.4.182 test-pool-w-4a88 None     TCP
backend      backend                                        198.18.0.40  test-pool-w-4f47 None     HBONE
client       client                                         198.18.2.198 test-pool-w-b539 None     HBONE
```

### 2. STRICT mTLS: 인증 없는 요청 거부
| 요청 | 결과 |
|---|---|
| client → backend | `200` |
| attacker(메시 밖) → backend | `000` (exit 56) |


```
$ kubectl apply -f strict-mtls.yaml
peerauthentication.security.istio.io/strict-mtls created

$ kubectl exec -n client client -- curl -s -o /dev/null -w "%{http_code}\n" backend.backend.svc.cluster.local
200

$ kubectl exec -n attacker attacker -- curl -s -o /dev/null -w "%{http_code}\n" --max-time 5 backend.backend.svc.cluster.local
000
command terminated with exit code 56
```

### 3. ztunnel 접근 로그: 신원 기반 판정
```
$ kubectl logs -n istio-system ztunnel-rsktp --tail=50 | grep -E "client|attacker"

2026-09-30T06:45:59.337908Z info access connection complete src.addr=198.18.2.198:44866 src.workload="client" src.namespace="client" src.identity="spiffe://cluster.local/ns/client/sa/default" src.cluster="Kubernetes" dst.addr=198.18.0.40:15008 dst.hbone_addr=198.18.0.40:80 dst.service="backend.backend.svc.cluster.local" dst.workload="backend" dst.namespace="backend" dst.identity="spiffe://cluster.local/ns/backend/sa/default" dst.cluster="Kubernetes" direction="inbound" bytes_sent=1134 bytes_recv=97 duration="1ms"

2026-09-30T06:45:59.689271Z error access connection complete src.addr=198.18.4.182:46376 src.workload="attacker" src.namespace="attacker" src.cluster="Kubernetes" dst.addr=198.18.0.40:80 dst.service="backend.backend.svc.cluster.local" dst.workload="backend" dst.namespace="backend" dst.cluster="Kubernetes" direction="inbound" bytes_sent=0 bytes_recv=0 duration="0ms" error="connection closed due to policy rejection: explicitly denied by: istio-system/istio_converted_static_strict"
```

### 4. AuthorizationPolicy: 인증됐지만 인가되지 않은 요청 거부
attacker를 메시에 편입해 인증서를 부여하면 STRICT만으로는 통과됨(`200`). 신원 기반 ALLOW 정책 적용 후 다시 차단

| 요청 | 결과 |
|---|---|
| client → backend | `200` |
| attacker(메시 안) → backend | `000` (exit 56) |

```
$ kubectl exec -n attacker attacker -- curl -s -o /dev/null -w "%{http_code}\n" --max-time 5 backend.backend.svc.cluster.local
200    # 메시 편입 후, AuthorizationPolicy 적용 전

$ kubectl apply -f allow-client-only.yaml
authorizationpolicy.security.istio.io/allow-client-only created

$ kubectl exec -n client client -- curl -s -o /dev/null -w "%{http_code}\n" backend.backend.svc.cluster.local
200

$ kubectl exec -n attacker attacker -- curl -s -o /dev/null -w "%{http_code}\n" --max-time 5 backend.backend.svc.cluster.local
000
command terminated with exit code 56
```

### 5. attacker 요청의 단계별 판정 (ztunnel 로그)

| 단계 | `src.identity` | 판정 |
|---|---|---|
| 메시 밖 | 없음 | 거부: `policy rejection: explicitly denied by: istio-system/istio_converted_static_strict` |
| 메시 편입 (인가 정책 없음) | `spiffe://cluster.local/ns/attacker/sa/default` | 허용 |
| AuthorizationPolicy 적용 | `spiffe://cluster.local/ns/attacker/sa/default` | 거부: `policy rejection: allow policies exist, but none allowed` |

```
$ kubectl logs -n istio-system ztunnel-rsktp --tail=20 | grep attacker

# ① 메시 밖: 신원 없음 → STRICT에 의해 거부
2026-09-30T06:45:59.689271Z error access connection complete src.addr=198.18.4.182:46376 src.workload="attacker" src.namespace="attacker" src.cluster="Kubernetes" dst.addr=198.18.0.40:80 dst.service="backend.backend.svc.cluster.local" dst.workload="backend" dst.namespace="backend" dst.cluster="Kubernetes" direction="inbound" bytes_sent=0 bytes_recv=0 duration="0ms" error="connection closed due to policy rejection: explicitly denied by: istio-system/istio_converted_static_strict"

# ② 메시 편입: 신원 있음, 인가 정책 없음 → 허용
2026-09-30T06:51:18.870753Z info access connection complete src.addr=198.18.4.182:41402 src.workload="attacker" src.namespace="attacker" src.identity="spiffe://cluster.local/ns/attacker/sa/default" src.cluster="Kubernetes" dst.addr=198.18.0.40:15008 dst.hbone_addr=198.18.0.40:80 dst.service="backend.backend.svc.cluster.local" dst.workload="backend" dst.namespace="backend" dst.identity="spiffe://cluster.local/ns/backend/sa/default" dst.cluster="Kubernetes" direction="inbound" bytes_sent=1134 bytes_recv=97 duration="1ms"

# ③ AuthorizationPolicy 적용: 신원 있음, 허용 대상 아님 → 거부
2026-09-30T06:52:38.432309Z error access connection complete src.addr=198.18.4.182:41402 src.workload="attacker" src.namespace="attacker" src.identity="spiffe://cluster.local/ns/attacker/sa/default" src.cluster="Kubernetes" dst.addr=198.18.0.40:15008 dst.hbone_addr=198.18.0.40:80 dst.service="backend.backend.svc.cluster.local" dst.workload="backend" dst.namespace="backend" dst.identity="spiffe://cluster.local/ns/backend/sa/default" dst.cluster="Kubernetes" direction="inbound" bytes_sent=0 bytes_recv=0 duration="0ms" error="connection closed due to policy rejection: allow policies exist, but none allowed"
```

### 확인된 사항
- **인증과 인가의 분리**: mTLS(STRICT)는 "신원을 증명했는가"만 판단하므로, 메시에 편입된 비인가 워크로드는 통과됨. 신원별 접근 권한은 AuthorizationPolicy로 별도 통제해야 함
- **신원 = 인증서**: 워크로드에는 ServiceAccount를 기반으로 한 SPIFFE 신원이 부여되며, AuthorizationPolicy의 `principals`에는 `cluster.local/ns/<namespace>/sa/<serviceaccount>`형태의 principal을 지정한다.
- **PeerAuthentication의 동작**: STRICT 설정이 ztunnel 내부에서 인가 정책(`istio_converted_static_strict`)으로 변환되어 평문 요청을 거부함
- **Cilium NetworkPolicy와의 차이**: cilium/kubernetes NetworkPolicy는 L3/L4에서 IP·엔드포인트·kubernetes 라벨 등을 기준으로 트래픽을 통제하는 반면, istio AuthorizationPolicy는 mTLS로 검증된 SPIEFFE기반 워크로드 신원을 정책 조건으로 사용할 수 있음. 이 테스트 구성에서는 cilium NetworkPolicy 차단 시 timeout(exit 28), istio는 인증서 신원 기준으로 연결을 능동 종료 connection reset/close(exit 56)형태로 관찰됨. → 위치를 신뢰하지 않고 신원으로 판단하는 제로 트러스트 방식
- **Ambient의 운영 이점**: 네임스페이스 라벨만으로 파드 재시작 없이 mTLS 적용
- **관리형 K8s 도입 리스크**: CNI 설정 주체가 클라우드 벤더인 환경에서는 서비스 메시 도입 시 기존 CNI·노드 커널 설정과의 호환성 검증이 선행되어야 함