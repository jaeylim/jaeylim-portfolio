### Docker Compose → K8s 전환 (Kompose)
기존 Docker Compose 기반으로 운영하던 Zammad 헬프데스크를 Kompose를 활용해 Kubernetes 매니페스트로 전환:

- Kompose로 기존 docker-compose.yml을 Deployment/Service/PVC 매니페스트로 1차 자동 변환
- PostgreSQL, Nginx, Websocket 등 컴포넌트별 리소스 분리 및 수동 보정
- 자동 변환 시 누락·오류가 발생하는 항목(볼륨 마운트 경로, 초기화 순서 등) 식별 및 수정

### Service Mesh (Istio Ambient Mode)
NKS(Kubernetes v1.36)에 Istio Ambient Mode(1.31)를 설치하고, STRICT mTLS와 신원 기반 AuthorizationPolicy로 서비스 간 인증·인가를 단계별로 검증:

- 네임스페이스 라벨만으로 파드 재시작 없이 메시 편입(HBONE mTLS 터널), STRICT mTLS로 메시 밖 평문 요청 거부
- 메시에 편입된 비인가 워크로드가 mTLS만으로는 통과됨을 확인 → ServiceAccount 기반 SPIFFE ID로 허용 대상을 제한하는 AuthorizationPolicy 적용 후 차단
- ztunnel 접근 로그로 요청별 신원(`src.identity`)과 거부 사유(인증 실패/인가 실패)를 구분해 검증
- 관리형 Cilium 환경 호환성 이슈 2건 해결: `cni-exclusive` 충돌(istio-cni 미기동), IPv4 전용 노드의 IPv6 처리 실패(ztunnel CrashLoop, 파드 편입 실패)

### 네트워크 정책 및 트래픽 가시성 (Cilium/Hubble)
NKS(Kubernetes v1.36) 환경에서 선언적 네트워크 정책(NetworkPolicy)으로 네임스페이스 간 접근통제를 구현하고, Hubble로 허용·차단 트래픽을 관측해 통제 동작을 검증:

- client / backend / attacker 네임스페이스 구성
- backend에 인바운드를 `client` 네임스페이스에서만 허용하는 화이트리스트 정책 적용 (명시 허용 외 트래픽은 기본 거부)
- 검증 결과: client → backend `FORWARDED`, attacker → backend 연결 타임아웃 및 Hubble 로그 `Policy denied` / `DROPPED` 확인
- NKS의 Cilium은 NCP 관리형으로 배포되어 `cilium hubble enable --ui` 적용이 불가 → NCP 공식 가이드 기반으로 Hubble Relay/UI를 별도 배포
- Hubble UI 서비스 맵을 통해 허용·차단 플로우 시각화

### Admission Control (Kyverno)
NKS(Kubernetes v1.36)에 Kyverno를 설치하고, 컨테이너 보안 기준을 정책 코드로 정의해 배포 단계에서 위반 워크로드를 차단:

- privileged 컨테이너 금지, root 실행 금지(runAsNonRoot 필수), 허용 레지스트리 외 이미지 차단 정책 3종을 `Enforce` 모드로 적용
- 위반 항목별 테스트 파드로 검증: 위반 파드 3종은 admission 단계에서 거부(정책명·필드 경로 포함 메시지 확인), 정상 파드만 생성
- 공유 클러스터 환경을 고려해 정책 적용 범위를 테스트 네임스페이스로 한정, 조건부 앵커로 오탐 방지
- 레거시 ClusterPolicy의 deprecation 및 CEL 기반 ValidatingPolicy 전환 흐름 확인

### KEDA 오토스케일링 성능 분석
메시지 브로커 4종을 대상으로 KEDA 기반 오토스케일링 성능을 비교 분석한 한양대학교 석사 논문(우수논문상 수상, KCI 등재) 관련 코드:

- 벤치마크 코드 및 실험 기록은 별도 레포에서 관리: [keda-broker-benchmark](https://github.com/jaeylim/keda-broker-benchmark) 본 포트폴리오 내 문서화는 진행 하지 않음. 
