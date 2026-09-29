### Docker Compose → K8s 전환 (Kompose)
기존 Docker Compose 기반으로 운영하던 Zammad 헬프데스크를 Kompose를 활용해 Kubernetes 매니페스트로 전환:

- Kompose로 기존 docker-compose.yml을 Deployment/Service/PVC 매니페스트로 1차 자동 변환
- PostgreSQL, Nginx, Websocket 등 컴포넌트별 리소스 분리 및 수동 보정
- 자동 변환 시 누락·오류가 발생하는 항목(볼륨 마운트 경로, 초기화 순서 등) 식별 및 수정

### Service Mesh (Istio Ambient Mode)
NCP Kubernetes Service(NKS) 클러스터에 Istio Ambient Mode를 설치하고, mTLS 강제 및 네임스페이스 간 트래픽 통제를 검증

### 네트워크 정책 및 트래픽 가시성 (Cilium/Hubble)
NKS(Kubernetes v1.36) 환경에서 선언적 네트워크 정책(NetworkPolicy)으로 네임스페이스 간 접근통제를 구현하고, Hubble로 허용·차단 트래픽을 관측해 통제 동작을 검증:

- client / backend / attacker 네임스페이스 구성
- backend에 인바운드를 `client` 네임스페이스에서만 허용하는 화이트리스트 정책 적용 (명시 허용 외 트래픽은 기본 거부)
- 검증 결과: client → backend `FORWARDED`, attacker → backend 연결 타임아웃 및 Hubble 로그 `Policy denied` / `DROPPED` 확인
- NKS의 Cilium은 NCP 관리형으로 배포되어 `cilium hubble enable --ui` 적용이 불가 → NCP 공식 가이드 기반으로 Hubble Relay/UI를 별도 배포
- Hubble UI 서비스 맵을 통해 허용·차단 플로우 시각화

### Admission Control (Kyverno)
> 기존 설정값 수정중

### KEDA 오토스케일링 성능 분석
메시지 브로커 4종을 대상으로 KEDA 기반 오토스케일링 성능을 비교 분석한 한양대학교 석사 논문(우수논문상 수상, KCI 등재) 관련 코드:

- 벤치마크 코드 및 실험 기록은 별도 레포에서 관리: [keda-broker-benchmark](https://github.com/jaeylim/keda-broker-benchmark) 본 포트폴리오 내 문서화는 진행 하지 않음. 
