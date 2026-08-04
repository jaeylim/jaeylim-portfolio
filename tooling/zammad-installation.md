### tooling-installation.md
NCP 인프라 (Rocky Linux 9.8) 위에 Zammad를 Docker Compose로 배포한 설치 기록

### 1. 서버 환경
- OS: Rocky Linux 9.8 (KVM)
- 용도: 보안팀 내부 헬프데스크 (기존 테스트 서버 구성 기준 재배포)

### 2. Docker 설치
Rocky Linux 기본 저장소에는 최신 Docker Engine이 포함되어 있지 않아, Docker 공식 저장소를 별도로 등록해 설치
```bash
# 기존 패키지 제거
sudo dnf remove -y docker docker-client docker-client-latest docker-common \
    docker-latest docker-latest-logrotate docker-logrotate docker-engine

# Docker 공식 저장소 추가
sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# Docker 설치
sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 서비스 시작 및 부팅 자동실행 등록
sudo systemctl enable --now docker

# 설치 확인
docker --version
docker compose version
```

### 3. Zammad 배포
공식 [zammad-docker-compose](https://github.com/zammad/zammad-docker-compose) 저장소를 기반으로 배포했다.

```bash
# git 설치 (없을 경우)
sudo dnf install -y git

# 공식 저장소 클론
git clone https://github.com/zammad/zammad-docker-compose.git
cd zammad-docker-compose

# 컨테이너 기동
docker compose up -d

# 컨테이너 상태 확인
docker ps
```
```
# 기동 컨테이너 (9개)
zammad-nginx -- 
zammad-scheduler
zammad-railsserver
zammad-backup
zammad-websocket
zammad-postgresql
zammad-redis
zammad-memcached
zammad-elasticsearch
```

### 4. Nginx 설치 및 프록시 설정
```bash
# Nginx (호스트) 설치
sudo dnf install -y nginx
sudo systemctl enable --now nginx

# 인증서 배치
sudo mkdir -p /etc/nginx/ssl
sudo cp <기존_인증서>.crt /etc/nginx/ssl/
sudo cp <기존_키>.key /etc/nginx/ssl/
sudo chmod 600 /etc/nginx/ssl/*.key

# (기존 인증서 사용할 경우 유효기간 확인)
openssl x509 -in /etc/nginx/ssl/<기존_인증서>.crt -noout -dates

# Reverse Proxy 설정
▸ /etc/nginx/conf.d/zammad-ssl.conf
server {
    listen 443 ssl;
    server_name <내부 도메인>;

    ssl_certificate     /etc/nginx/ssl/<기존_인증서>.crt;
    ssl_certificate_key /etc/nginx/ssl/<기존_키>.key;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# 설정 검증 후 재시작
sudo nginx -t
sudo systemctl restart nginx

```

### 5. 커스터마이징 (.env)
공식 compose 파일은 기본값으로 동작하며, 리버스 프록시/SSO 연동을 위해 아래 환경변수를 `.env`에 커스터마이징.

1) scheme 설정 (https)
2) 컨테이너 재시작 (docker compose up -d)

```env
NGINX_SERVER_SCHEME=https
ZAMMAD_FQDN=<내부 도메인>
RAILS_TRUSTED_PROXIES=<호스트 Nginx 대역>
```

※ compose 파일 전체는 공식 저장소 원본을 그대로 사용했으며, 위 환경변수만 실제 배포 환경에 맞게 재정의했다. 상세 아키텍처/트러블슈팅은 [README.md](./README.md) 참고.
