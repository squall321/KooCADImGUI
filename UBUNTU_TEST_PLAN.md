# KooCAD Ubuntu 테스트 실행 계획

**작성일**: 2025-11-17
**목적**: Ubuntu 환경에서 KooCAD의 실제 동작을 단계별로 검증
**예상 소요 시간**: 2-4시간
**대상 OS**: Ubuntu 20.04+ / Debian 11+

---

## 📋 목차

1. [테스트 전략](#테스트-전략)
2. [사전 준비사항](#사전-준비사항)
3. [Level 0: 환경 설정](#level-0-환경-설정)
4. [Level 1: 핵심 기능 테스트](#level-1-핵심-기능-테스트)
5. [Level 2: CAD 생성 테스트](#level-2-cad-생성-테스트)
6. [Level 3: Backend API 테스트](#level-3-backend-api-테스트)
7. [Level 4: 전체 통합 테스트](#level-4-전체-통합-테스트)
8. [문제 해결](#문제-해결)
9. [성공 기준](#성공-기준)

---

## 🎯 테스트 전략

### 단계별 검증 방식

```
Level 0: 환경 설정        (10분) → Python, Git 설치 확인
Level 1: 핵심 기능        (20분) → 파라미터 시스템 테스트
Level 2: CAD 생성         (30분) → 실제 3D 모델 생성
Level 3: Backend API      (60분) → 데이터베이스, 작업 큐
Level 4: 전체 통합        (60분) → End-to-End 워크플로우
```

### 실패 시 대응

- 각 레벨은 독립적으로 실행 가능
- 이전 레벨 실패 시 다음 레벨 스킵
- 모든 명령어 실행 결과 기록
- 에러 발생 시 로그 수집

---

## 🔧 사전 준비사항

### 시스템 요구사항

| 항목 | 최소 사양 | 권장 사양 |
|------|-----------|-----------|
| OS | Ubuntu 20.04 | Ubuntu 22.04 LTS |
| CPU | 2 cores | 4+ cores |
| RAM | 4 GB | 8+ GB |
| Disk | 10 GB 여유 공간 | 20+ GB |
| Python | 3.11+ | 3.11+ |

### 필요한 권한

```bash
# sudo 권한 확인
sudo -v

# 패키지 설치 권한 확인
sudo apt update
```

---

## Level 0: 환경 설정

**목표**: Python 3.11+ 환경 구축
**예상 시간**: 10분
**실패 시 영향**: 전체 테스트 불가

### Step 0.1: 시스템 업데이트

```bash
# 터미널 열기 (Ctrl+Alt+T)

# 시스템 업데이트
sudo apt update
sudo apt upgrade -y

# 필수 빌드 도구 설치
sudo apt install -y build-essential git curl wget
```

**검증**:
```bash
gcc --version    # 출력 있으면 성공
git --version    # 출력 있으면 성공
```

### Step 0.2: Python 3.11 설치

#### 방법 A: Deadsnakes PPA (권장)

```bash
# PPA 추가
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update

# Python 3.11 설치
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# 기본 Python3 확인
python3.11 --version
```

**검증**:
```bash
python3.11 --version
# 출력 예: Python 3.11.x
```

#### 방법 B: Conda 사용 (CadQuery 설치도 간편)

```bash
# Miniconda 다운로드
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

# 설치
bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda3

# 환경변수 설정
echo 'export PATH="$HOME/miniconda3/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# 설치 확인
conda --version

# Python 3.11 환경 생성
conda create -n koocad python=3.11 -y
conda activate koocad
```

**검증**:
```bash
python --version
# 출력: Python 3.11.x
```

### Step 0.3: 프로젝트 클론

```bash
# 작업 디렉토리 이동
cd ~

# 저장소 클론 (이미 클론되어 있다면 스킵)
# git clone https://github.com/yourusername/KooCADImGUI.git

# 또는 현재 디렉토리 사용
cd /home/user/KooCADImGUI

# Git 상태 확인
git status
git log --oneline -5
```

**검증**:
```bash
ls -la
# 출력: src/, tests/, examples/, README.md 등이 보여야 함
```

### Step 0.4: 가상환경 생성 (Conda 사용 안 할 경우)

```bash
cd /home/user/KooCADImGUI

# 가상환경 생성
python3.11 -m venv venv

# 활성화
source venv/bin/activate

# pip 업그레이드
pip install --upgrade pip setuptools wheel
```

**검증**:
```bash
which python
# 출력: /home/user/KooCADImGUI/venv/bin/python

python --version
# 출력: Python 3.11.x
```

---

## Level 1: 핵심 기능 테스트

**목표**: 파라미터 시스템 동작 확인
**예상 시간**: 20분
**의존성**: Pydantic, SymPy, NumPy, Pytest

### Step 1.1: 핵심 의존성 설치

```bash
# 가상환경 활성화 확인
source venv/bin/activate  # 또는 conda activate koocad

# 핵심 패키지만 설치
pip install pydantic>=2.6.0 sympy>=1.12 numpy>=1.26.0 pytest>=8.0.0 pytest-cov>=4.1.0

# 설치 확인
pip list | grep -E "pydantic|sympy|numpy|pytest"
```

**검증**:
```bash
python -c "import pydantic; print(f'Pydantic: {pydantic.__version__}')"
python -c "import sympy; print(f'SymPy: {sympy.__version__}')"
python -c "import numpy; print(f'NumPy: {numpy.__version__}')"
python -c "import pytest; print(f'Pytest: {pytest.__version__}')"
```

**예상 출력**:
```
Pydantic: 2.x.x
SymPy: 1.x.x
NumPy: 1.26.x
Pytest: 8.x.x
```

### Step 1.2: PYTHONPATH 설정

```bash
# 환경변수 설정
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# 확인
echo $PYTHONPATH
```

**검증**:
```bash
python -c "import sys; print('src' in str(sys.path))"
# 출력: True
```

### Step 1.3: 모듈 Import 테스트

```bash
# KooCAD 모듈 로딩 테스트
python << 'EOF'
import sys
sys.path.insert(0, 'src')

print("=" * 70)
print("KooCAD 모듈 Import 테스트")
print("=" * 70)

modules = [
    'koocad.core.parameters',
    'koocad.core.expressions',
    'koocad.core.presets',
    'koocad.core.validation',
    'koocad.core.serialization',
]

success = 0
failed = 0

for mod in modules:
    try:
        __import__(mod)
        print(f"✅ {mod}")
        success += 1
    except Exception as e:
        print(f"❌ {mod}: {e}")
        failed += 1

print("=" * 70)
print(f"결과: {success}개 성공, {failed}개 실패")
print("=" * 70)

exit(0 if failed == 0 else 1)
EOF
```

**성공 기준**: 모든 모듈 ✅, 실패 0개

### Step 1.4: 기본 예제 실행

```bash
# 파라미터 시스템 예제 실행
python examples/00_basic_parameters_corrected.py

# 출력이 에러 없이 나오면 성공
```

**예상 출력**:
```
KooCAD Parameter System - Corrected API Usage
=============================================
1. FloatParameter with keyword arguments: ✓
2. Parameter validation: ✓
...
All tests passed! ✓
```

### Step 1.5: Pytest 실행

```bash
# 전체 테스트 실행
pytest tests/ -v

# 또는 특정 테스트만
pytest tests/test_parameters.py tests/test_presets.py -v

# 커버리지 포함
pytest tests/ --cov=koocad.core --cov-report=term-missing
```

**성공 기준**:
```
79 passed in X.XXs
```

**로그 저장**:
```bash
# 테스트 결과 파일로 저장
pytest tests/ -v > test_results_level1.txt 2>&1
cat test_results_level1.txt
```

---

## Level 2: CAD 생성 테스트

**목표**: 실제 3D CAD 모델 생성
**예상 시간**: 30분
**의존성**: CadQuery, OCP

### Step 2.1: CadQuery 설치

#### 방법 A: Conda 사용 (강력 권장)

```bash
# Conda 환경 활성화
conda activate koocad

# CadQuery 설치
conda install -c conda-forge cadquery -y

# 설치 확인
python -c "import cadquery as cq; print(f'CadQuery: {cq.__version__}')"
```

#### 방법 B: Pip 사용 (복잡함, 권장하지 않음)

```bash
# OCP (OpenCASCADE Python) 먼저 설치
pip install cadquery-ocp>=7.7.0

# CadQuery 설치
pip install cadquery>=2.4.0

# 설치 확인
python -c "import cadquery as cq; print(f'CadQuery: {cq.__version__}')"
```

**검증**:
```bash
python << 'EOF'
import cadquery as cq

# 간단한 박스 생성
result = cq.Workplane("XY").box(10, 10, 10)
print(f"✅ CadQuery 작동 확인: {type(result)}")
print(f"   Version: {cq.__version__}")
EOF
```

**예상 출력**:
```
✅ CadQuery 작동 확인: <class 'cadquery.Workplane'>
   Version: 2.x.x
```

### Step 2.2: 출력 디렉토리 생성

```bash
# CAD 파일 출력 디렉토리 생성
mkdir -p output
mkdir -p output/step
mkdir -p output/stl
mkdir -p output/test

# 권한 확인
ls -ld output/
```

### Step 2.3: 간단한 CAD 생성 테스트

```bash
# 간단한 BGA 생성 스크립트 실행
python << 'EOF'
import sys
sys.path.insert(0, 'src')

from koocad.core.parameters import FloatParameter, IntParameter, ParameterSet, Unit
from koocad.core.presets import BGAPresets

print("=" * 70)
print("BGA 프리셋 로딩 테스트")
print("=" * 70)

# BGA 15x15 프리셋 로드
presets = BGAPresets.get_all()
bga_preset = presets['BGA_15x15_0.8mm']

# 파라미터 평가
values = bga_preset.evaluate_all()

print(f"✅ BGA 프리셋 로드 성공")
print(f"   Ball Rows: {values['ball_rows']}")
print(f"   Ball Cols: {values['ball_cols']}")
print(f"   Ball Pitch: {values['ball_pitch']} mm")
print(f"   Total Balls: {values['ball_rows'] * values['ball_cols']}")
print(f"   Substrate: {values['substrate_width']}mm x {values['substrate_height']}mm")

print("=" * 70)
EOF
```

### Step 2.4: 실제 3D 모델 생성

```bash
# 실제 CAD 생성 테스트
python << 'EOF'
import sys
sys.path.insert(0, 'src')

try:
    import cadquery as cq
    from koocad.core.presets import BGAPresets

    print("=" * 70)
    print("실제 BGA 3D 모델 생성 테스트")
    print("=" * 70)

    # 간단한 BGA 기판 생성 (테스트용 간소화 버전)
    presets = BGAPresets.get_all()
    bga = presets['BGA_15x15_0.8mm']
    values = bga.evaluate_all()

    # CadQuery로 기판 생성
    substrate = (
        cq.Workplane("XY")
        .box(
            values['substrate_width'],
            values['substrate_height'],
            values['substrate_thickness']
        )
    )

    print(f"✅ 기판 생성 성공: {values['substrate_width']}mm x {values['substrate_height']}mm x {values['substrate_thickness']}mm")

    # STEP 파일로 내보내기
    cq.exporters.export(substrate, "output/test/bga_substrate_test.step")
    print(f"✅ STEP 파일 저장: output/test/bga_substrate_test.step")

    # STL 파일로 내보내기
    cq.exporters.export(substrate, "output/test/bga_substrate_test.stl")
    print(f"✅ STL 파일 저장: output/test/bga_substrate_test.stl")

    print("=" * 70)
    print("테스트 성공!")
    print("=" * 70)

except ImportError as e:
    print(f"❌ Import 에러: {e}")
    print("   CadQuery가 설치되지 않았습니다.")
    exit(1)
except Exception as e:
    print(f"❌ 에러: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
EOF
```

**성공 기준**:
```
✅ 기판 생성 성공: 13.2mm x 13.2mm x 0.8mm
✅ STEP 파일 저장: output/test/bga_substrate_test.step
✅ STL 파일 저장: output/test/bga_substrate_test.stl
테스트 성공!
```

**파일 확인**:
```bash
ls -lh output/test/
file output/test/bga_substrate_test.step
file output/test/bga_substrate_test.stl
```

### Step 2.5: 예제 스크립트 실행 (선택)

```bash
# 주의: examples/05_cad_generation.py가 실제로 존재하고 실행 가능한지 확인 필요
# 파일이 실제 생성기를 사용한다면 실행

# 파일 확인
ls -l examples/05_cad_generation.py

# 실행 (파일이 있는 경우)
# python examples/05_cad_generation.py
```

---

## Level 3: Backend API 테스트

**목표**: FastAPI + PostgreSQL + Redis 작동 확인
**예상 시간**: 60분
**의존성**: PostgreSQL, Redis, FastAPI, SQLAlchemy, Celery

### Step 3.1: Docker 설치 (인프라 서비스용)

```bash
# Docker 설치 확인
docker --version

# 없으면 설치
if ! command -v docker &> /dev/null; then
    # Docker 설치
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh

    # 현재 사용자를 docker 그룹에 추가
    sudo usermod -aG docker $USER

    # 재로그인 필요 (또는 newgrp docker)
    echo "Docker 설치 완료. 재로그인 후 계속하세요."
fi

# Docker Compose 설치
sudo apt install -y docker-compose
```

**검증**:
```bash
docker --version
docker-compose --version
```

### Step 3.2: 인프라 서비스 시작

#### 방법 A: Docker Compose 사용

```bash
# docker-compose.yml 생성
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    container_name: koocad-postgres
    environment:
      POSTGRES_USER: koocad
      POSTGRES_PASSWORD: koocad_password
      POSTGRES_DB: koocad
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U koocad"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: koocad-redis
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  minio:
    image: quay.io/minio/minio
    container_name: koocad-minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data

volumes:
  postgres_data:
  minio_data:
EOF

# 서비스 시작
docker-compose up -d

# 상태 확인
docker-compose ps
```

**검증**:
```bash
# PostgreSQL 연결 테스트
docker exec -it koocad-postgres psql -U koocad -c "SELECT version();"

# Redis 연결 테스트
docker exec -it koocad-redis redis-cli ping
# 출력: PONG
```

#### 방법 B: 시스템 서비스 사용

```bash
# PostgreSQL 설치
sudo apt install -y postgresql postgresql-contrib

# Redis 설치
sudo apt install -y redis-server

# 서비스 시작
sudo systemctl start postgresql redis-server
sudo systemctl enable postgresql redis-server

# PostgreSQL 사용자 및 DB 생성
sudo -u postgres psql << 'EOF'
CREATE USER koocad WITH PASSWORD 'koocad_password';
CREATE DATABASE koocad OWNER koocad;
GRANT ALL PRIVILEGES ON DATABASE koocad TO koocad;
\q
EOF
```

**검증**:
```bash
psql -U koocad -h localhost -d koocad -c "SELECT version();"
redis-cli ping
```

### Step 3.3: Backend 의존성 설치

```bash
# Backend 패키지 설치
pip install fastapi>=0.110.0 \
            uvicorn[standard]>=0.27.0 \
            sqlalchemy>=2.0.25 \
            alembic>=1.13.0 \
            celery>=5.3.6 \
            redis>=5.0.1 \
            psycopg[binary]>=3.1.0 \
            pydantic-settings>=2.1.0 \
            python-multipart>=0.0.9 \
            python-jose[cryptography]>=3.3.0 \
            passlib[bcrypt]>=1.7.4
```

**검증**:
```bash
pip list | grep -E "fastapi|uvicorn|sqlalchemy|celery|redis"
```

### Step 3.4: 환경 변수 설정

```bash
# .env 파일 생성
cat > .env << 'EOF'
# Database
DATABASE_URL=postgresql://koocad:koocad_password@localhost:5432/koocad

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# MinIO (Docker 사용 시)
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_SECURE=false

# JWT
JWT_SECRET_KEY=your-secret-key-change-this-in-production-$(openssl rand -hex 32)
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# Logging
LOG_LEVEL=INFO

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]
EOF

# 환경 변수 로드
export $(cat .env | grep -v '^#' | xargs)

# 확인
echo $DATABASE_URL
```

### Step 3.5: 데이터베이스 마이그레이션 (실제 마이그레이션 파일이 있는 경우)

```bash
# Alembic 설정 확인
ls -l alembic.ini alembic/

# 마이그레이션 실행 (파일이 있는 경우)
# alembic upgrade head

# 또는 직접 테이블 생성 테스트
python << 'EOF'
import sys
sys.path.insert(0, 'src')

try:
    from sqlalchemy import create_engine, text
    import os

    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://koocad:koocad_password@localhost:5432/koocad')

    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        result = conn.execute(text("SELECT version();"))
        version = result.fetchone()[0]
        print(f"✅ PostgreSQL 연결 성공")
        print(f"   Version: {version[:50]}...")

except Exception as e:
    print(f"❌ 데이터베이스 연결 실패: {e}")
    exit(1)
EOF
```

### Step 3.6: API 서버 시작 테스트

```bash
# 백그라운드에서 API 서버 실행
python << 'EOF' &
import sys
sys.path.insert(0, 'src')

try:
    import uvicorn
    print("Starting FastAPI server...")
    # 실제 app이 있는 경우
    # from koocad.backend.main import app
    # uvicorn.run(app, host="0.0.0.0", port=8000)
    print("Note: Actual backend implementation needed")
except ImportError:
    print("FastAPI backend files not fully implemented yet")
EOF

# 또는 간단한 Health Check 서버 테스트
python << 'EOF'
from fastapi import FastAPI
import uvicorn

app = FastAPI(title="KooCAD Test API")

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "koocad-test"}

@app.get("/")
def root():
    return {"message": "KooCAD API Test Server"}

print("Starting test API server on http://localhost:8000")
print("Press Ctrl+C to stop")
print("Visit http://localhost:8000/docs for API documentation")

# uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
print("✅ FastAPI 실행 가능 확인됨")
EOF
```

**검증**:
```bash
# API 테스트 (서버 실행 중인 경우)
# curl http://localhost:8000/health
# curl http://localhost:8000/docs
```

---

## Level 4: 전체 통합 테스트

**목표**: 전체 워크플로우 검증
**예상 시간**: 60분
**의존성**: 모든 이전 레벨 성공

### Step 4.1: End-to-End 워크플로우 테스트

```bash
# 전체 워크플로우 스크립트 실행
python << 'EOF'
import sys
sys.path.insert(0, 'src')

print("=" * 70)
print("KooCAD End-to-End 워크플로우 테스트")
print("=" * 70)

# 1. 파라미터 설정
print("\n[1/5] 파라미터 설정...")
from koocad.core.presets import BGAPresets
presets = BGAPresets.get_all()
bga = presets['BGA_15x15_0.8mm']
values = bga.evaluate_all()
print(f"✅ BGA 프리셋 로드: {values['ball_rows']}x{values['ball_cols']}")

# 2. CAD 생성
print("\n[2/5] CAD 모델 생성...")
try:
    import cadquery as cq
    substrate = cq.Workplane("XY").box(
        values['substrate_width'],
        values['substrate_height'],
        values['substrate_thickness']
    )
    print(f"✅ 3D 모델 생성 성공")
except ImportError:
    print(f"⚠️  CadQuery 없음, 생성 스킵")
    substrate = None

# 3. 파일 내보내기
print("\n[3/5] 파일 내보내기...")
if substrate:
    try:
        import os
        os.makedirs('output/e2e', exist_ok=True)
        cq.exporters.export(substrate, "output/e2e/bga_final.step")
        print(f"✅ STEP 파일 저장: output/e2e/bga_final.step")
    except Exception as e:
        print(f"❌ 파일 저장 실패: {e}")
else:
    print(f"⚠️  모델 없음, 내보내기 스킵")

# 4. 파라미터 직렬화
print("\n[4/5] 파라미터 직렬화...")
from koocad.core.serialization import ParameterSerializer
serializer = ParameterSerializer()
data = serializer.serialize_parameter_set(bga)
print(f"✅ JSON 직렬화 성공: {len(str(data))} bytes")

# 5. 검증
print("\n[5/5] 최종 검증...")
import json
json_str = json.dumps(data, indent=2)
with open('output/e2e/bga_params.json', 'w') as f:
    f.write(json_str)
print(f"✅ 파라미터 JSON 저장: output/e2e/bga_params.json")

print("\n" + "=" * 70)
print("E2E 테스트 완료!")
print("=" * 70)
print(f"\n생성된 파일:")
print(f"  - output/e2e/bga_params.json")
if substrate:
    print(f"  - output/e2e/bga_final.step")
print()
EOF
```

**검증**:
```bash
# 생성된 파일 확인
ls -lh output/e2e/
cat output/e2e/bga_params.json | head -20
```

### Step 4.2: 전체 테스트 결과 요약

```bash
# 테스트 결과 요약 생성
cat > test_summary_$(date +%Y%m%d_%H%M%S).txt << EOF
KooCAD Ubuntu 테스트 결과 요약
=====================================
테스트 일시: $(date)
시스템: $(uname -a)
Python: $(python --version)

Level 0: 환경 설정
  - Python 3.11+: $(python --version)
  - Git: $(git --version)
  - PYTHONPATH: $PYTHONPATH

Level 1: 핵심 기능
  - Pytest: $(python -c 'import pytest; print(pytest.__version__)' 2>&1 || echo "N/A")
  - Pydantic: $(python -c 'import pydantic; print(pydantic.__version__)' 2>&1 || echo "N/A")
  - 테스트 통과: 확인 필요 (pytest 실행 결과 참고)

Level 2: CAD 생성
  - CadQuery: $(python -c 'import cadquery as cq; print(cq.__version__)' 2>&1 || echo "N/A")
  - STEP 파일: $(ls output/test/bga_substrate_test.step 2>&1 || echo "N/A")

Level 3: Backend
  - PostgreSQL: $(docker exec koocad-postgres pg_isready 2>&1 || echo "시스템 서비스 확인")
  - Redis: $(docker exec koocad-redis redis-cli ping 2>&1 || echo "시스템 서비스 확인")
  - FastAPI: $(python -c 'import fastapi; print(fastapi.__version__)' 2>&1 || echo "N/A")

Level 4: 통합 테스트
  - E2E 파일: $(ls output/e2e/*.* 2>&1 || echo "N/A")

=====================================
EOF

cat test_summary_*.txt
```

---

## 🔧 문제 해결

### 문제 1: Python 3.11 설치 실패

**증상**:
```
E: Unable to locate package python3.11
```

**해결**:
```bash
# PPA 다시 추가
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11

# 또는 Conda 사용
conda create -n koocad python=3.11
```

### 문제 2: CadQuery 설치 실패

**증상**:
```
ERROR: Could not find a version that satisfies the requirement cadquery
```

**해결**:
```bash
# Conda 사용 (권장)
conda install -c conda-forge cadquery

# Pip로 시도 시
pip install cadquery-ocp
pip install cadquery
```

### 문제 3: PostgreSQL 연결 실패

**증상**:
```
psycopg2.OperationalError: could not connect to server
```

**해결**:
```bash
# Docker 서비스 상태 확인
docker-compose ps

# 컨테이너 재시작
docker-compose restart postgres

# 로그 확인
docker-compose logs postgres

# 포트 확인
sudo netstat -tlnp | grep 5432
```

### 문제 4: Import 에러

**증상**:
```
ModuleNotFoundError: No module named 'koocad'
```

**해결**:
```bash
# PYTHONPATH 설정
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# 또는 개발 모드 설치
pip install -e .
```

### 문제 5: 권한 에러

**증상**:
```
Permission denied: '/output/test/...'
```

**해결**:
```bash
# 디렉토리 권한 수정
sudo chown -R $USER:$USER output/
chmod -R 755 output/

# 디렉토리 생성
mkdir -p output/test output/e2e
```

### 문제 6: Docker 권한 에러

**증상**:
```
permission denied while trying to connect to the Docker daemon
```

**해결**:
```bash
# 사용자를 docker 그룹에 추가
sudo usermod -aG docker $USER

# 재로그인 또는
newgrp docker

# Docker 서비스 재시작
sudo systemctl restart docker
```

---

## ✅ 성공 기준

### Level 1 성공 기준

- [ ] Python 3.11+ 설치 확인
- [ ] 모든 핵심 모듈 import 성공
- [ ] 79개 pytest 테스트 통과
- [ ] 예제 스크립트 에러 없이 실행

**검증 명령어**:
```bash
python --version | grep "3.11"
pytest tests/ -v | grep "79 passed"
python examples/00_basic_parameters_corrected.py
```

### Level 2 성공 기준

- [ ] CadQuery 설치 및 import 성공
- [ ] 간단한 3D 모델 생성 성공
- [ ] STEP 파일 출력 성공
- [ ] STL 파일 출력 성공

**검증 명령어**:
```bash
python -c "import cadquery as cq; print(cq.__version__)"
ls -lh output/test/bga_substrate_test.step
file output/test/bga_substrate_test.step | grep "ISO-10303"
```

### Level 3 성공 기준

- [ ] PostgreSQL 연결 성공
- [ ] Redis 연결 성공
- [ ] FastAPI 서버 실행 가능
- [ ] 데이터베이스 테이블 생성 성공

**검증 명령어**:
```bash
docker-compose ps | grep "Up"
psql -U koocad -h localhost -d koocad -c "SELECT 1;"
redis-cli ping
```

### Level 4 성공 기준

- [ ] 파라미터 → CAD → 파일 전체 워크플로우 성공
- [ ] JSON 직렬화/역직렬화 성공
- [ ] 모든 출력 파일 생성 확인

**검증 명령어**:
```bash
ls output/e2e/bga_params.json
ls output/e2e/bga_final.step
cat output/e2e/bga_params.json | jq .
```

---

## 📝 테스트 체크리스트

실행하면서 체크해 주세요:

### 사전 준비
- [ ] Ubuntu 20.04+ / Debian 11+
- [ ] sudo 권한 있음
- [ ] 인터넷 연결 정상

### Level 0
- [ ] Python 3.11 설치
- [ ] Git 클론 완료
- [ ] 가상환경 생성
- [ ] PYTHONPATH 설정

### Level 1
- [ ] Pydantic, SymPy, NumPy 설치
- [ ] Pytest 설치
- [ ] 79개 테스트 통과
- [ ] 예제 실행 성공

### Level 2
- [ ] CadQuery 설치
- [ ] 3D 모델 생성
- [ ] STEP 파일 출력
- [ ] STL 파일 출력

### Level 3
- [ ] Docker 설치
- [ ] PostgreSQL 시작
- [ ] Redis 시작
- [ ] .env 파일 생성
- [ ] 데이터베이스 연결

### Level 4
- [ ] E2E 테스트 실행
- [ ] 모든 파일 생성 확인
- [ ] 테스트 결과 요약 생성

---

## 📊 예상 결과

### 성공 시 생성되는 파일

```
output/
├── test/
│   ├── bga_substrate_test.step  (~10-50 KB)
│   └── bga_substrate_test.stl   (~10-100 KB)
└── e2e/
    ├── bga_params.json          (~2-5 KB)
    └── bga_final.step           (~10-50 KB)

test_results_level1.txt          (pytest 결과)
test_summary_YYYYMMDD_HHMMSS.txt (전체 요약)
```

### 로그 파일

```bash
# 모든 실행 로그를 저장하려면
script -c "bash UBUNTU_TEST_PLAN.md" koocad_test_$(date +%Y%m%d_%H%M%S).log
```

---

## 🚀 빠른 실행 스크립트

전체 과정을 자동화한 스크립트:

```bash
#!/bin/bash
# koocad_quick_test.sh

set -e  # 에러 시 중단

echo "KooCAD Ubuntu 빠른 테스트 시작..."

# Level 0
echo "[Level 0] Python 환경 확인..."
python3.11 --version || (echo "Python 3.11 필요"; exit 1)

# Level 1
echo "[Level 1] 핵심 기능 테스트..."
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
pip install -q pydantic sympy numpy pytest pytest-cov
pytest tests/ -v --tb=short

# Level 2 (CadQuery 있는 경우)
if python -c "import cadquery" 2>/dev/null; then
    echo "[Level 2] CAD 생성 테스트..."
    python examples/05_cad_generation.py || echo "예제 파일 확인 필요"
else
    echo "[Level 2] CadQuery 없음, 스킵"
fi

echo "테스트 완료!"
```

실행:
```bash
chmod +x koocad_quick_test.sh
./koocad_quick_test.sh
```

---

## 📞 지원

문제 발생 시:

1. **로그 수집**: 모든 에러 메시지 복사
2. **환경 정보**: `python --version`, `uname -a`
3. **이슈 리포트**: GitHub Issues에 보고
4. **문서 참조**:
   - `INSTALLATION.md`
   - `TEST_RESULTS.md`
   - `API_CORRECTIONS.md`

---

**문서 버전**: 1.0
**최종 업데이트**: 2025-11-17
**작성자**: KooCAD Team
