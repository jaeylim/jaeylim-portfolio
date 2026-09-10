### Docker Compose → K8s 전환 (Kompose)

기존 Docker Compose 기반으로 운영하던 Zammad 헬프데스크를 Kompose를 활용해 Kubernetes 매니페스트로 전환:

- Kompose로 기존 docker-compose.yml을 Deployment/Service/PVC 매니페스트로 1차 자동 변환
- PostgreSQL, Nginx, Websocket 등 컴포넌트별 리소스 분리 및 수동 보정
- 자동 변환 시 누락·오류가 발생하는 항목(볼륨 마운트 경로, 초기화 순서 등) 식별 및 수정

### Service Mesh (Istio Ambient Mode)

NCP Kubernetes Service(NKS) 클러스터에 Istio Ambient Mode를 설치하고, mTLS 강제 및 네임스페이스 간 트래픽 통제를 검증:

### KEDA 오토스케일링 성능 분석

메시지 브로커 4종을 대상으로 KEDA 기반 오토스케일링 성능을 비교 분석한 한양대학교 석사 논문(우수논문상 수상, KCI 등재) 관련 코드:

- 벤치마크 코드 및 실험 기록은 별도 레포에서 관리: [keda-broker-benchmark](https://github.com/jaeylim/keda-broker-benchmark) 본 포트폴리오 내 문서화는 진행 하지 않음. 