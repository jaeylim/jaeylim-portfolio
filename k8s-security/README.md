### Kubernetes 보안·장애 대응

#### 서비스 메시 구성 (Istio Ambient Mode)

NKS(Naver Kubernetes Service)는 Ambient Mode를 공식 지원하지 않아, istioctl/Helm으로 istiod·ztunnel·base·istio-cni를 직접 설치. Kiali로 서비스 간 트래픽 흐름을, Prometheus로 메트릭을 확인.

#### 클러스터 운영 가시성

Rancher/Lens를 연결하여 관리형 Kubernetes 클러스터의 Pod/Node 상태를 모니터링.

#### 리소스 설정 장애 대응

일부 Pod에 resource request·limit이 누락되어 특정 노드에 부하가 집중되는 상황 발견. 전체 워크로드를 점검하여 누락된 설정을 일괄 정비. 이후 해당 원인으로 인한 노드 OOM 미발생 확인.

#### 장애 시나리오 설계·검증 (2026.03 ~ 2026.06)

서버 환경 장애 5종, Kubernetes 환경 장애 5종을 설계하고 트러블슈팅 검증을 수행.

- Kubernetes: Node NotReady, OOMKilled, Probe(Liveness/Readiness/Startup) 오류, PVC Pending, Ingress 설정 오류
- 서버: (구체적 시나리오 목록은 별도 문서로 정리 예정)

#### 자격

CKA (Certified Kubernetes Administrator)
