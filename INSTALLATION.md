# KooCAD 설치 가이드

**버전**: 0.1.0
**Python 요구사항**: 3.11+
**플랫폼**: Linux, macOS, Windows

---

## 📋 목차

- [빠른 시작](#빠른-시작)
- [단계별 설치](#단계별-설치)
- [설치 레벨](#설치-레벨)
- [의존성 세부사항](#의존성-세부사항)
- [문제 해결](#문제-해결)
- [확인 및 테스트](#확인-및-테스트)

---

## ⚡ 빠른 시작

### 최소 설치 (파라미터 시스템만)

```bash
# 1. 저장소 클론
git clone https://github.com/yourusername/KooCADImGUI.git
cd KooCADImGUI

# 2. 가상환경 생성 (권장)
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 핵심 의존성만 설치
pip install pydantic sympy numpy pytest

# 4. 테스트 실행
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
pytest tests/test_parameters.py -v
```

**결과**: 파라미터 시스템, 표현식 엔진, 프리셋 라이브러리 사용 가능 ✅

---

## 🔧 단계별 설치

### Step 1: Python 환경 준비

#### Python 3.11+ 설치 확인
```bash
python3 --version  # 3.11 이상이어야 함
```

#### Python 3.11 설치 (필요한 경우)

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev
```

**macOS (Homebrew):**
```bash
brew install python@3.11
```

**Windows:**
- [Python 공식 사이트](https://www.python.org/downloads/)에서 다운로드

### Step 2: 저장소 클론

```bash
git clone https://github.com/yourusername/KooCADImGUI.git
cd KooCADImGUI
```

### Step 3: 가상환경 생성 및 활성화

```bash
# 가상환경 생성
python3.11 -m venv venv

# 활성화
source venv/bin/activate        # Linux/macOS
# 또는
venv\Scripts\activate           # Windows
```

### Step 4: 의존성 설치 (레벨 선택)

설치 레벨에 따라 선택하세요 👇

---

## 🎚️ 설치 레벨

### 레벨 0: 핵심 기능만 (권장 시작점)

**포함 기능**:
- ✅ 파라미터 시스템 (Float, Int, Bool, String, Expression)
- ✅ 표현식 엔진 (SymPy)
- ✅ 프리셋 라이브러리 (BGA, MLCC, Resistor)
- ✅ 검증 및 직렬화
- ✅ 40개 단위 테스트

**설치 명령어**:
```bash
pip install pydantic>=2.6.0 sympy>=1.12 numpy>=1.26.0 pytest>=8.0.0 pytest-cov>=4.1.0
```

**테스트**:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
pytest tests/test_parameters.py tests/test_presets.py -v
```

**예제 실행**:
```bash
python examples/00_basic_parameters_corrected.py
python examples/01_basic_parameters.py
```

---

### 레벨 1: CAD 생성 기능 추가

**추가 기능**:
- ✅ CadQuery를 이용한 3D CAD 모델 생성
- ✅ BGA/MLCC/Inductor 생성기
- ✅ STEP/STL 내보내기

**설치 명령어**:
```bash
# Conda 사용 (강력 권장)
conda install -c conda-forge cadquery

# 또는 pip (더 복잡함)
pip install cadquery>=2.4.0
```

**CadQuery 설치 문제 해결**:

CadQuery는 복잡한 의존성(OpenCASCADE)을 가지고 있어 conda 사용을 강력히 권장합니다.

```bash
# Conda가 없는 경우 Miniconda 설치
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# CadQuery 설치
conda create -n koocad python=3.11
conda activate koocad
conda install -c conda-forge cadquery
```

**테스트**:
```bash
python -c "import cadquery as cq; print('CadQuery version:', cq.__version__)"
```

**예제 실행**:
```bash
python examples/05_cad_generation.py
```

---

### 레벨 2: 백엔드 API 기능

**추가 기능**:
- ✅ FastAPI REST API 서버
- ✅ JWT 인증
- ✅ Celery 작업 큐
- ✅ PostgreSQL 데이터베이스
- ✅ Redis 캐싱
- ✅ WebSocket 실시간 통신

**시스템 요구사항**:
```bash
# Ubuntu/Debian
sudo apt install postgresql-15 redis-server

# macOS
brew install postgresql@15 redis

# 서비스 시작
sudo systemctl start postgresql redis-server  # Linux
brew services start postgresql@15 redis        # macOS
```

**설치 명령어**:
```bash
pip install -e ".[dev]"
```

또는 개별 설치:
```bash
pip install fastapi>=0.110.0 \
            uvicorn[standard]>=0.27.0 \
            sqlalchemy>=2.0.25 \
            celery>=5.3.6 \
            redis>=5.0.1 \
            psycopg[binary]>=3.1.0
```

**데이터베이스 설정**:
```bash
# PostgreSQL 데이터베이스 생성
sudo -u postgres createuser koocad
sudo -u postgres createdb koocad
sudo -u postgres psql -c "ALTER USER koocad WITH PASSWORD 'your_password';"

# 환경변수 설정
cat > .env << EOF
DATABASE_URL=postgresql://koocad:your_password@localhost/koocad
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=$(openssl rand -hex 32)
EOF

# 마이그레이션 실행
alembic upgrade head
```

**서버 실행**:
```bash
# API 서버
uvicorn koocad.backend.main:app --reload

# Celery 워커
celery -A koocad.backend.celery_app worker -l info
```

---

### 레벨 3: UI 기능

**추가 기능**:
- ✅ DearPyGui 노드 에디터
- ✅ 3D 프리뷰
- ✅ 파라미터 인스펙터

**설치 명령어**:
```bash
pip install dearpygui>=1.11.0 pillow>=10.2.0 moderngl>=5.9.0
```

**UI 실행**:
```bash
python -m koocad.ui.app
```

---

### 레벨 4: 메싱 및 시뮬레이션

**추가 기능**:
- ✅ Gmsh 메싱
- ✅ LS-DYNA 키워드 생성
- ✅ 메시 품질 체크

**설치 명령어**:
```bash
# Ubuntu/Debian
sudo apt install gmsh

# macOS
brew install gmsh

# Python 바인딩
pip install gmsh>=4.12.0 meshio>=5.3.0
```

**테스트**:
```bash
python examples/11_export_meshing_demo.py
```

---

### 레벨 5: HPC 배치 처리 (전체 설치)

**추가 기능**:
- ✅ Slurm 배치 작업
- ✅ Apptainer 컨테이너
- ✅ 파라미터 스윕

**시스템 요구사항**:
```bash
# Slurm 설치 (HPC 클러스터)
sudo apt install slurm-wlm  # Ubuntu/Debian

# Apptainer 설치
sudo apt install apptainer   # Ubuntu 22.04+
```

**전체 설치**:
```bash
pip install -e ".[all]"
```

**HPC 예제**:
```bash
python examples/12_hpc_batch_demo.py
```

---

## 📦 의존성 세부사항

### 필수 의존성 (레벨 0)

| 패키지 | 버전 | 용도 |
|--------|------|------|
| pydantic | ≥2.6.0 | 파라미터 검증 |
| sympy | ≥1.12 | 표현식 평가 |
| numpy | ≥1.26.0 | 수치 계산 |
| pytest | ≥8.0.0 | 테스트 |

### 선택적 의존성

| 패키지 | 버전 | 용도 | 레벨 |
|--------|------|------|------|
| cadquery | ≥2.4.0 | CAD 생성 | 1 |
| fastapi | ≥0.110.0 | REST API | 2 |
| dearpygui | ≥1.11.0 | 노드 UI | 3 |
| gmsh | ≥4.12.0 | 메싱 | 4 |
| slurm-wlm | - | HPC 배치 | 5 |

---

## 🔍 확인 및 테스트

### 설치 확인 스크립트

```bash
python3 << 'EOF'
import sys
sys.path.insert(0, 'src')

print("=" * 70)
print("KooCAD 설치 확인")
print("=" * 70)

# 레벨 0: 핵심
packages = [
    ('pydantic', 'Pydantic'),
    ('sympy', 'SymPy'),
    ('numpy', 'NumPy'),
    ('pytest', 'Pytest'),
]

for module, name in packages:
    try:
        mod = __import__(module)
        version = getattr(mod, '__version__', 'unknown')
        print(f"✅ {name}: v{version}")
    except ImportError:
        print(f"❌ {name}: 미설치")

# KooCAD 모듈
print("\n" + "=" * 70)
print("KooCAD 모듈 확인")
print("=" * 70)

modules = [
    'koocad.core.parameters',
    'koocad.core.expressions',
    'koocad.core.presets',
]

for mod in modules:
    try:
        __import__(mod)
        print(f"✅ {mod}")
    except Exception as e:
        print(f"❌ {mod}: {e}")

print("\n" + "=" * 70)
EOF
```

### 테스트 실행

```bash
# 전체 테스트
pytest tests/ -v

# 특정 레벨 테스트
pytest tests/test_parameters.py -v  # 레벨 0
pytest tests/test_presets.py -v     # 레벨 0

# 커버리지 포함
pytest tests/ --cov=koocad.core --cov-report=html
```

### 예제 실행

```bash
# 레벨 0 예제
python examples/00_basic_parameters_corrected.py
python examples/01_basic_parameters.py
python examples/03_test_data_generation.py

# 레벨 1 예제 (CadQuery 필요)
python examples/05_cad_generation.py

# 레벨 2 예제 (Backend 필요)
python examples/10_backend_api_demo.py
```

---

## ❓ 문제 해결

### CadQuery 설치 실패

**문제**: `pip install cadquery` 실패

**해결**:
```bash
# 방법 1: Conda 사용 (권장)
conda install -c conda-forge cadquery

# 방법 2: Docker 사용
docker pull cadquery/cadquery:latest
```

### Import 에러

**문제**: `ModuleNotFoundError: No module named 'koocad'`

**해결**:
```bash
# PYTHONPATH 설정
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# 또는 개발 모드로 설치
pip install -e .
```

### Pydantic 경고

**문제**: `PydanticDeprecatedSince20` 경고

**해결**: 이 경고는 현재 무시해도 됩니다. 모든 기능이 정상 작동합니다. 향후 Pydantic V2 API로 마이그레이션 예정입니다.

### PostgreSQL 연결 실패

**문제**: `connection refused`

**해결**:
```bash
# PostgreSQL 실행 확인
sudo systemctl status postgresql

# 시작
sudo systemctl start postgresql

# 연결 테스트
psql -U koocad -d koocad -h localhost
```

### 테스트 실패

**문제**: 일부 테스트 실패

**해결**:
```bash
# 의존성 재설치
pip install --upgrade pydantic sympy numpy

# 캐시 삭제
rm -rf .pytest_cache __pycache__

# 다시 테스트
pytest tests/ -v --tb=short
```

---

## 📚 다음 단계

설치 완료 후:

1. **[빠른 시작 가이드](QUICKSTART.md)** - 5분 안에 시작하기
2. **[예제 둘러보기](examples/)** - 실전 예제 코드
3. **[API 문서](API_CORRECTIONS.md)** - 올바른 API 사용법
4. **[테스트 결과](TEST_RESULTS.md)** - 검증된 기능 확인

---

## 🆘 추가 도움

- **문서**: [README.md](README.md)
- **테스트 결과**: [TEST_RESULTS.md](TEST_RESULTS.md)
- **API 가이드**: [API_CORRECTIONS.md](API_CORRECTIONS.md)
- **이슈 리포트**: GitHub Issues

---

**마지막 업데이트**: 2025-11-10
**버전**: 0.1.0
**테스트 상태**: ✅ 40/40 passing
