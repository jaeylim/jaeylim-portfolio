### Docker Compose → Kubernetes 전환 (kompose)

### 목적
Docker Compose 기반으로 운영 중인 Zammad 테스트 서버를 대상으로, `kompose`를 이용해 Compose 정의를 Kubernetes 매니페스트로 변환하는 과정과 발생하는 이슈 확인

### 대상 서비스 구조
기존 `zammad-docker-compose` 구성:
- `zammad-railsserver`, `zammad-scheduler`, `zammad-websocket`, `zammad-nginx`, `zammad-init` (같은 이미지, 역할별 command 분리)
- `zammad-postgresql`, `zammad-redis`, `zammad-memcached`, `zammad-elasticsearch`
- `zammad-backup` (백업 전용)

### kompose convert 오류
1) 버전 이슈
```
ERRO Could not parse config for project zammaddockercompose : Unsupported config option for services service: 'zammad-init'
...
FATA composeObject.Parse() failed
```
[원인] Compose 파일이 YAML anchor(`&zammad-service`)와 `x-shared` 확장 필드를 사용하고 있고,
Docker Compose(v5.1.4)가 생성하는 최신 스펙 문법(`depends_on.required`, `volumes[].volume: {}` 등)을 kompose 1.26.0(2년 이상 지난 버전)이 파싱 못함.

### kompose convert 결과 (.yaml)
kompose 최신 버전(1.38.0)으로 업그레이드 후 k8s 오브젝트 생성 확인
```bash
curl -L https://github.com/kubernetes/kompose/releases/download/v1.38.0/kompose-linux-amd64 -o kompose
chmod +x kompose
sudo mv ./kompose /usr/local/bin/kompose
```

### 결과
- Deployment: `zammad-backup`, `zammad-elasticsearch`, `zammad-memcached`, `zammad-nginx`, `zammad-postgresql`, `zammad-railsserver`, `zammad-redis`, `zammad-scheduler`, `zammad-websocket`
- Pod: `zammad-init` (compose의 `restart: on-failure`를 kompose가 1회성 작업으로 판단해 Deployment가 아닌 단발 Pod로 변환)
- PVC: `zammad-backup`, `zammad-storage`, `elasticsearch-data`, `postgresql-data`, `redis-data`
- Service: `zammad-nginx` 단 하나만 생성됨

### Service 오브젝트 누락
kompose는 compose 파일에 `ports`/`expose`가 정의된 서비스에만 k8s Service를 생성.
`zammad-nginx`만 `expose: 8080`이 있었기 때문에, `zammad-postgresql`/`zammad-redis`/`zammad-memcached` 등은 Service 없이 Pod만 생성됨. 이 상태로는 railsserver 등이 `zammad-postgresql` 같은 호스트명으로 DNS 조회를 할 수 없어 연결 실패되므로 수동으로 Service 추가 필요.

### zammad-storage 공유 볼륨과 RWX 요구사항
`docker-compose.yml`을 YAML 파싱(anchor/alias 반영)해서 확인한 결과,
`zammad-storage` 볼륨(`/opt/zammad/storage`)을 아래 서비스가 동시에 공유:
```
zammad-backup, zammad-init, zammad-nginx, zammad-railsserver, zammad-scheduler, zammad-websocket
```
이 중 railsserver/scheduler/websocket/nginx는 상시 실행되며 동시에 파일을 읽고 쓰므로
ReadWriteMany(RWX)가 필요. NFS 서버 + `nfs-subdir-external-provisioner` 조합 등 별도 StorageClass 구성이 필요. 반면 `postgresql-data`/`redis-data`/`elasticsearch-data`는 각각 단일 서비스만 사용하므로 RWO로 충분하다고 판단됨.

### 원본 볼륨 구조 확인 (참고)
기존 테스트 서버의 `zammad-docker-compose_postgresql-data` 볼륨은 `docker volume inspect` 결과 `/var/lib/docker/volumes/...` 아래에 위치하며, `lsblk`/`df -h` 확인 결과 별도 블록스토리지가 아닌 인스턴스 디스크(단일) 위에 올라가 있는 구조임을 확인.

### 참고
- 이 실습은 기존 운영 중인 Zammad 테스트 서버(Docker Compose)와 완전히 분리된 별도 네임스페이스/클러스터에서 진행하며, 기존 서버에는 영향을 주지 않음.

### 추가 (k8s:secret)
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/
kubectl version --client

#### dry-run (base64)
```bash
kubectl create secret generic zammad-postgresql-secret \
  --from-literal=POSTGRES_DB=zammad_production \
  --from-literal=POSTGRES_USER=zammad \
  --from-literal=POSTGRES_PASSWORD=zammad \
  --from-literal=POSTGRESQL_HOST=zammad-postgresql \
  --from-literal=POSTGRESQL_PORT=5432 \
  --from-literal=POSTGRESQL_DB=zammad_production \
  --from-literal=POSTGRESQL_USER=zammad \
  --from-literal=POSTGRESQL_PASS=zammad \
  --from-literal=POSTGRESQL_OPTIONS='?pool=50' \
  --dry-run=client -o yaml > zammad-postgresql-secret.yaml
```
kompose가 만든 Deployment들(zammad-railsserver-deployment.yaml, zammad-scheduler-deployment.yaml, zammad-websocket-deployment.yaml, zammad-nginx-deployment.yaml, zammad-postgresql-deployment.yaml, zammad-backup-deployment.yaml, zammad-init-pod.yaml)를 열어보면 env: 안에 이런 식으로 평문이 있음.

```yaml
env:
  - name: POSTGRESQL_HOST
    value: zammad-postgresql
  - name: POSTGRESQL_PASS
    value: zammad
  ...
```

이 항목들을 지우고 그 자리에 아래처럼 envFrom을 추가하면, Secret에 있는 키들이 전부 환경변수로 자동 주입할 수 있음:

```yaml
spec:
  containers:
    - name: zammad-railsserver
      image: ghcr.io/zammad/zammad:7.0.1-0053
      envFrom:
        - secretRef:
            name: zammad-postgresql-secret
      env:
        - name: TZ
          value: Europe/Berlin
        # postgres 관련 아닌 나머지 env는 그대로 유지  
```