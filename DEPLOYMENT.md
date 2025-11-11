# 프로덕션 배포 가이드

KooCAD를 프로덕션 환경에 배포하는 방법입니다.

## 📋 목차

- [배포 전 체크리스트](#배포-전-체크리스트)
- [배포 아키텍처](#배포-아키텍처)
- [Docker Compose 배포](#docker-compose-배포)
- [Kubernetes 배포](#kubernetes-배포)
- [HPC 환경 배포](#hpc-환경-배포)
- [모니터링 & 로깅](#모니터링--로깅)
- [보안 설정](#보안-설정)
- [백업 & 복구](#백업--복구)
- [트러블슈팅](#트러블슈팅)

---

## 배포 전 체크리스트

### ✅ 코드 품질

- [ ] 모든 테스트 통과 (79/79 tests)
- [ ] 코드 커버리지 80% 이상
- [ ] Lint/타입 체크 통과
- [ ] Security 스캔 통과 (bandit, pip-audit)

### ✅ 인프라

- [ ] PostgreSQL 15+ 준비
- [ ] Redis 7+ 준비
- [ ] MinIO 또는 S3 준비
- [ ] 도메인 및 SSL 인증서
- [ ] 백업 스토리지 확보

### ✅ 보안

- [ ] 환경 변수 암호화
- [ ] Secret 관리 시스템 (Vault, AWS Secrets Manager)
- [ ] 방화벽 규칙 설정
- [ ] Rate limiting 설정
- [ ] CORS 정책 검토

### ✅ 모니터링

- [ ] Prometheus + Grafana 설정
- [ ] 로그 수집 (ELK, Loki)
- [ ] Alerting 규칙 설정
- [ ] Uptime 모니터링

---

## 배포 아키텍처

### 소규모 배포 (1-10 사용자)

```
┌─────────────────┐
│  Nginx (Reverse │
│  Proxy + SSL)   │
└────────┬────────┘
         │
┌────────▼───────────────────────────────────┐
│  Docker Compose                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │ FastAPI  │  │PostgreSQL│  │  Redis   │ │
│  │ (4 pods) │  │          │  │          │ │
│  └──────────┘  └──────────┘  └──────────┘ │
│  ┌──────────┐  ┌──────────┐               │
│  │  Celery  │  │  MinIO   │               │
│  │ Workers  │  │          │               │
│  └──────────┘  └──────────┘               │
└────────────────────────────────────────────┘
```

### 중규모 배포 (10-100 사용자)

```
┌─────────────┐
│ Load        │
│ Balancer    │
└──────┬──────┘
       │
┌──────▼──────────────────────────────────┐
│  Kubernetes Cluster                     │
│  ┌────────────┐  ┌────────────┐        │
│  │  FastAPI   │  │  Celery    │        │
│  │  Pods (10) │  │  Workers(5)│        │
│  └────────────┘  └────────────┘        │
└─────────────────────────────────────────┘
       │              │
┌──────▼──────┐  ┌───▼────┐  ┌─────────┐
│ RDS/Cloud   │  │ Redis  │  │   S3    │
│ PostgreSQL  │  │ Cluster│  │  Bucket │
└─────────────┘  └────────┘  └─────────┘
```

### 대규모 배포 (100+ 사용자, HPC)

```
┌─────────────┐
│ CDN +       │
│ WAF         │
└──────┬──────┘
       │
┌──────▼───────────────────────────────────┐
│  Multi-Region Kubernetes                 │
│  ┌──────────────┐  ┌──────────────┐     │
│  │ Region US    │  │ Region EU    │     │
│  │ (FastAPI×20) │  │ (FastAPI×20) │     │
│  └──────────────┘  └──────────────┘     │
└──────────────────────────────────────────┘
       │                    │
┌──────▼────────┐    ┌──────▼─────────┐
│ Aurora Global │    │ Redis          │
│ Database      │    │ Sentinel       │
└───────────────┘    └────────────────┘
       │
┌──────▼──────────────────────────────┐
│  HPC Cluster (Slurm + Apptainer)    │
│  - Compute nodes: 100+              │
│  - CAD generation jobs              │
│  - Parameter sweep simulations      │
└─────────────────────────────────────┘
```

---

## Docker Compose 배포

### 1. 환경 변수 설정

```bash
# 프로덕션 환경 변수 생성
cp .env.example .env.production

# 편집
nano .env.production
```

**중요 변경사항:**
```bash
# .env.production
APP_ENV=production
DEBUG=false
SECRET_KEY=<strong-random-key-512-bits>
JWT_SECRET_KEY=<another-strong-random-key>

# Strong passwords
DATABASE_PASSWORD=<strong-db-password>
REDIS_PASSWORD=<strong-redis-password>
MINIO_SECRET_KEY=<strong-minio-password>

# Disable auto-reload
API_RELOAD=false

# Production URLs
API_CORS_ORIGINS=https://koocad.yourcompany.com

# Logging
LOG_LEVEL=WARNING
LOG_FORMAT=json

# Rate limiting (stricter)
RATE_LIMIT_PER_MINUTE=30
```

### 2. SSL 인증서 준비

```bash
# Let's Encrypt 사용
sudo apt install certbot
sudo certbot certonly --standalone -d koocad.yourcompany.com

# 인증서 경로
# /etc/letsencrypt/live/koocad.yourcompany.com/fullchain.pem
# /etc/letsencrypt/live/koocad.yourcompany.com/privkey.pem
```

### 3. Nginx 설정

```nginx
# /etc/nginx/sites-available/koocad
upstream koocad_api {
    server localhost:8000;
}

server {
    listen 80;
    server_name koocad.yourcompany.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name koocad.yourcompany.com;

    ssl_certificate /etc/letsencrypt/live/koocad.yourcompany.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/koocad.yourcompany.com/privkey.pem;

    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    client_max_body_size 100M;

    location / {
        proxy_pass http://koocad_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws {
        proxy_pass http://koocad_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 4. 서비스 시작

```bash
# Nginx 활성화
sudo ln -s /etc/nginx/sites-available/koocad /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Docker Compose 시작
docker-compose --env-file .env.production up -d

# 로그 확인
docker-compose logs -f
```

### 5. 데이터베이스 마이그레이션

```bash
# 컨테이너 내부에서 실행
docker-compose exec koocad-api alembic upgrade head

# 초기 데이터 생성 (선택)
docker-compose exec koocad-api python scripts/init_db.py
```

### 6. 헬스 체크

```bash
# API 상태 확인
curl https://koocad.yourcompany.com/health

# 데이터베이스 연결 확인
curl https://koocad.yourcompany.com/ready

# 메트릭 확인
curl https://koocad.yourcompany.com/metrics
```

---

## Kubernetes 배포

### 1. Namespace 생성

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: koocad
```

```bash
kubectl apply -f namespace.yaml
```

### 2. Secrets 생성

```bash
# PostgreSQL credentials
kubectl create secret generic postgres-secret \
  --from-literal=username=koocad \
  --from-literal=password=<strong-password> \
  --namespace=koocad

# Redis password
kubectl create secret generic redis-secret \
  --from-literal=password=<strong-password> \
  --namespace=koocad

# MinIO credentials
kubectl create secret generic minio-secret \
  --from-literal=access-key=koocad \
  --from-literal=secret-key=<strong-password> \
  --namespace=koocad

# JWT secret
kubectl create secret generic jwt-secret \
  --from-literal=secret-key=<strong-jwt-key> \
  --namespace=koocad
```

### 3. ConfigMap 생성

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: koocad-config
  namespace: koocad
data:
  APP_ENV: "production"
  LOG_LEVEL: "WARNING"
  DATABASE_HOST: "postgres-service"
  DATABASE_PORT: "5432"
  REDIS_HOST: "redis-service"
  REDIS_PORT: "6379"
  MINIO_ENDPOINT: "minio-service:9000"
```

### 4. Deployment - FastAPI

```yaml
# deployment-api.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: koocad-api
  namespace: koocad
spec:
  replicas: 3
  selector:
    matchLabels:
      app: koocad-api
  template:
    metadata:
      labels:
        app: koocad-api
    spec:
      containers:
      - name: api
        image: your-registry/koocad:0.2.0
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: koocad-config
        env:
        - name: DATABASE_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: jwt-secret
              key: secret-key
        resources:
          requests:
            cpu: "500m"
            memory: "512Mi"
          limits:
            cpu: "2000m"
            memory: "2Gi"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: koocad-api-service
  namespace: koocad
spec:
  selector:
    app: koocad-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

### 5. HorizontalPodAutoscaler

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: koocad-api-hpa
  namespace: koocad
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: koocad-api
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### 6. Ingress (SSL)

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: koocad-ingress
  namespace: koocad
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - koocad.yourcompany.com
    secretName: koocad-tls
  rules:
  - host: koocad.yourcompany.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: koocad-api-service
            port:
              number: 80
```

---

## HPC 환경 배포

상세 내용은 [HPC_DEPLOYMENT.md](HPC_DEPLOYMENT.md) 참조

### Apptainer 이미지 빌드

```bash
# 개발 환경에서 빌드
sudo apptainer build koocad.sif koocad.def

# HPC 클러스터로 전송
scp koocad.sif user@hpc.yourcluster.edu:/shared/containers/
```

### Slurm 작업 제출

```bash
# Parameter sweep 실행
sbatch --array=1-100 slurm/parameter_sweep.sbatch

# 작업 모니터링
squeue -u $USER
sacct -j JOBID --format=JobID,JobName,State,Elapsed,MaxRSS
```

---

## 모니터링 & 로깅

### Prometheus + Grafana

```bash
# 모니터링 스택 시작
docker-compose --profile monitoring up -d

# Grafana 접속: http://localhost:3000
# Username: admin
# Password: koocad_grafana_password
```

**주요 메트릭:**
- CAD 생성 시간 (histogram)
- API 요청 수 (counter)
- 데이터베이스 쿼리 시간
- Celery 작업 큐 길이
- 메모리/CPU 사용률

### 로그 수집 (ELK Stack)

```bash
# Elasticsearch + Kibana
docker run -d --name elasticsearch \
  -p 9200:9200 -p 9300:9300 \
  -e "discovery.type=single-node" \
  elasticsearch:8.10.0

# Logstash
docker run -d --name logstash \
  -p 5000:5000 \
  -v $(pwd)/config/logstash.conf:/usr/share/logstash/pipeline/logstash.conf \
  logstash:8.10.0
```

---

## 보안 설정

### 1. 방화벽 규칙

```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw deny 5432/tcp  # PostgreSQL (internal only)
sudo ufw deny 6379/tcp  # Redis (internal only)
sudo ufw enable
```

### 2. Rate Limiting

FastAPI에서 설정:
```python
# API rate limiting 활성화
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=30
```

### 3. Secret 암호화

```bash
# Vault 사용
vault kv put secret/koocad \
  db_password=<password> \
  jwt_secret=<secret>

# AWS Secrets Manager
aws secretsmanager create-secret \
  --name koocad/production \
  --secret-string file://secrets.json
```

---

## 백업 & 복구

### PostgreSQL 백업

```bash
# 자동 백업 스크립트
cat > /usr/local/bin/backup-koocad-db.sh <<'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=/backup/koocad
mkdir -p $BACKUP_DIR

docker-compose exec -T postgres pg_dump -U koocad koocad | \
  gzip > $BACKUP_DIR/koocad_${DATE}.sql.gz

# S3로 업로드
aws s3 cp $BACKUP_DIR/koocad_${DATE}.sql.gz \
  s3://your-backup-bucket/koocad/

# 7일 이상 된 백업 삭제
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
EOF

chmod +x /usr/local/bin/backup-koocad-db.sh

# Cron 등록 (매일 2AM)
echo "0 2 * * * /usr/local/bin/backup-koocad-db.sh" | crontab -
```

### 복구

```bash
# 백업 복원
gunzip < koocad_20251110.sql.gz | \
  docker-compose exec -T postgres psql -U koocad koocad
```

---

## 트러블슈팅

### API 응답 없음

```bash
# 로그 확인
docker-compose logs -f koocad-api

# 컨테이너 상태
docker-compose ps

# 네트워크 연결
docker-compose exec koocad-api ping postgres
```

### 데이터베이스 연결 실패

```bash
# PostgreSQL 로그
docker-compose logs postgres

# 연결 테스트
docker-compose exec koocad-api python -c \
  "from sqlalchemy import create_engine; \
   engine = create_engine('postgresql://koocad:password@postgres:5432/koocad'); \
   print(engine.execute('SELECT 1').scalar())"
```

### Celery 작업 실패

```bash
# Celery 로그
docker-compose logs celery-worker

# Redis 연결 확인
docker-compose exec redis redis-cli ping

# 작업 큐 확인
docker-compose exec koocad-api python -c \
  "from celery import Celery; \
   app = Celery('koocad', broker='redis://redis:6379/0'); \
   print(app.control.inspect().active())"
```

---

## 성능 튜닝

### PostgreSQL

```sql
-- postgresql.conf
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 16MB
maintenance_work_mem = 128MB
max_connections = 100
```

### Redis

```conf
# redis.conf
maxmemory 512mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

### Celery

```python
# Celery configuration
CELERY_WORKER_CONCURRENCY=8
CELERY_WORKER_PREFETCH_MULTIPLIER=2
CELERY_TASK_TIME_LIMIT=1800  # 30분
CELERY_TASK_SOFT_TIME_LIMIT=1500  # 25분
```

---

## 체크리스트: 배포 완료

- [ ] 모든 서비스 정상 실행
- [ ] SSL 인증서 설치 및 HTTPS 작동
- [ ] 데이터베이스 마이그레이션 완료
- [ ] 백업 자동화 설정
- [ ] 모니터링 대시보드 구성
- [ ] 알람 규칙 설정
- [ ] 문서화 완료
- [ ] 팀 교육 완료

---

**문의**: dev@koocad.com
**긴급 상황**: [On-Call 가이드](docs/ONCALL.md)
