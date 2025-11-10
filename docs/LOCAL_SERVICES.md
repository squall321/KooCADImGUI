# KooCAD Local Development Services Setup

Since we're using Apptainer for containerization, you'll need to run supporting services (PostgreSQL, Redis, MinIO) locally or on your infrastructure.

## Option 1: System Services (Recommended for HPC)

### PostgreSQL
```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql

# Create database
sudo -u postgres createuser koocad
sudo -u postgres createdb koocad -O koocad
sudo -u postgres psql -c "ALTER USER koocad PASSWORD 'your_password';"
```

### Redis
```bash
# Ubuntu/Debian
sudo apt install redis-server
sudo systemctl start redis-server
```

### MinIO (S3-compatible storage)
```bash
# Download binary
wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio
sudo mv minio /usr/local/bin/

# Create data directory
sudo mkdir -p /var/lib/minio/data

# Run as service (create systemd unit)
sudo tee /etc/systemd/system/minio.service <<EOF
[Unit]
Description=MinIO
After=network.target

[Service]
Type=notify
ExecStart=/usr/local/bin/minio server /var/lib/minio/data --console-address :9001
Restart=always
Environment="MINIO_ROOT_USER=koocad"
Environment="MINIO_ROOT_PASSWORD=your_password"

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl start minio
sudo systemctl enable minio
```

## Option 2: Docker for Local Services Only

If you're developing locally (not on HPC), you can use Docker just for infrastructure:

```bash
# Run only infrastructure services
docker run -d --name koocad-postgres \
  -e POSTGRES_USER=koocad \
  -e POSTGRES_PASSWORD=koocad_dev \
  -e POSTGRES_DB=koocad \
  -p 5432:5432 \
  postgres:16-alpine

docker run -d --name koocad-redis \
  -p 6379:6379 \
  redis:7-alpine

docker run -d --name koocad-minio \
  -e MINIO_ROOT_USER=koocad \
  -e MINIO_ROOT_PASSWORD=koocad_dev \
  -p 9000:9000 -p 9001:9001 \
  minio/minio server /data --console-address ":9001"
```

## Environment Configuration

Create `.env` file:
```bash
cp .env.example .env
```

Edit `.env`:
```bash
DATABASE_URL=postgresql://koocad:your_password@localhost:5432/koocad
REDIS_URL=redis://localhost:6379/0
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=koocad
MINIO_SECRET_KEY=your_password
MINIO_SECURE=false
```

## HPC Module Setup (if available)

Many HPC systems provide modules:
```bash
module load postgresql/15
module load redis/7
module load minio/latest
```

## Verification

```bash
# Test PostgreSQL
psql -h localhost -U koocad -d koocad -c "SELECT version();"

# Test Redis
redis-cli ping

# Test MinIO
curl http://localhost:9000/minio/health/live
```
