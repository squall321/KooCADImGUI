# KooCAD - Parametric Electronic Component CAD System

<div align="center">

![KooCAD Logo](docs/images/logo.png)

**완전 파라메트릭 전자부품 CAD 자동화 플랫폼**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Tests](https://img.shields.io/badge/tests-40%20passed-success.svg)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-core%20modules-brightgreen.svg)](TEST_RESULTS.md)

[Features](#features) • [Quick Start](#quick-start) • [Documentation](docs/) • [Examples](examples/)

</div>

---

## 🎯 프로젝트 개요

KooCAD는 전자부품(BGA, WLP, 수동소자 등)의 **완전 파라메트릭 3D CAD 모델**을 자동으로 생성하는 시스템입니다.

### 핵심 특징

- 🔧 **완전 파라메트릭**: 모든 치수가 수식/제약조건으로 연결
- 🎨 **노드 기반 UI**: DearPyGui 노드 에디터로 직관적 워크플로우
- ⚡ **하이브리드 Kernel**: CadQuery(빠름) + OCCT C++(강력함)
- 📦 **전자부품 전문**: BGA, WLP, MLCC, Inductor 등 라이브러리 내장
- 🚀 **HPC 배치 생성**: Slurm + Apptainer로 대량 파라미터 스윕
- 🔄 **FEA 파이프라인**: Gmsh/Netgen 메싱 → LS-DYNA 변환

---

## 🏗️ 아키텍처

```
┌─────────────────────────────────────────────────┐
│  Frontend: DearPyGui Node Editor                │
├─────────────────────────────────────────────────┤
│  API: FastAPI + WebSocket                       │
├─────────────────────────────────────────────────┤
│  Kernels: CadQuery (Py) | OCCT (C++/pybind11)  │
├─────────────────────────────────────────────────┤
│  Export: STEP/IGES/STL/GLB + Mesh               │
├─────────────────────────────────────────────────┤
│  Batch: Slurm + Apptainer (JSON param sweep)    │
├─────────────────────────────────────────────────┤
│  Storage: PostgreSQL + MinIO (Data Lake)        │
└─────────────────────────────────────────────────┘
```

자세한 내용: [ARCHITECTURE.md](ARCHITECTURE.md)

---

## 🚀 Quick Start

### 요구사항

**개발 환경:**
- Python 3.11+
- Apptainer (Singularity) 1.1+
- PostgreSQL 15+, Redis 7+, MinIO

**HPC 환경:**
- Slurm workload manager
- Apptainer 지원
- (Optional) InfiniBand, GPU

### 설치

#### 로컬 개발

```bash
# 1. Clone repository
git clone https://github.com/yourusername/KooCADImGUI.git
cd KooCADImGUI

# 2. 인프라 서비스 시작 (PostgreSQL, Redis, MinIO)
# 옵션 A: 시스템 서비스 사용 (권장 for HPC)
sudo systemctl start postgresql redis-server minio

# 옵션 B: Docker로 로컬 서비스만 실행
docker run -d --name koocad-postgres -p 5432:5432 \
    -e POSTGRES_USER=koocad -e POSTGRES_DB=koocad postgres:16-alpine

# 자세한 내용: docs/LOCAL_SERVICES.md

# 3. Apptainer 컨테이너 빌드
bash scripts/build-containers.sh

# 4. 개발용 컨테이너로 진입
apptainer shell --bind $(pwd)/src:/opt/koocad/src koocad-dev.sif

# 5. (컨테이너 내부) 데이터베이스 마이그레이션
alembic upgrade head

# 6. API 서버 실행
apptainer exec koocad-dev.sif koocad-server
```

#### HPC 배치 실행

```bash
# 파라미터 스윕 생성
koocad sweep generate --config sweep_config.yaml --output /scratch/params/

# Slurm job array 제출
sbatch scripts/slurm-batch-job.sh
```

### 첫 번째 CAD 생성

```python
from koocad.core.parameters import FloatParameter, IntParameter, ParameterSet, Unit
from koocad.core.presets import BGAPresets

# 방법 1: 프리셋 사용 (권장)
params = BGAPresets.get_all()['BGA_15x15_0.8mm']

# 방법 2: 커스텀 파라미터 정의
params = ParameterSet()
params.add(FloatParameter(name='substrate_width', value=12.0, unit=Unit.MM))
params.add(FloatParameter(name='substrate_height', value=12.0, unit=Unit.MM))
params.add(FloatParameter(name='substrate_thickness', value=0.8, unit=Unit.MM))
params.add(FloatParameter(name='ball_pitch', value=0.8, unit=Unit.MM))
params.add(FloatParameter(name='ball_diameter', value=0.4, unit=Unit.MM))
params.add(IntParameter(name='ball_rows', value=15))
params.add(IntParameter(name='ball_cols', value=15))

# 파라미터 검증 및 평가
values = params.evaluate_all()
print(f"Ball count: {values['ball_rows'] * values['ball_cols']}")

# CAD 생성 (CadQuery 필요)
# from koocad.generators.bga import BGAGenerator
# generator = BGAGenerator(parameters=params)
# shape = generator.generate()
# shape.export_step("my_bga.step")
```

---

## 📚 문서

- [Master Plan](MASTER_PLAN.md) - 145 Phase 전체 계획 ✅
- [Test Results](TEST_RESULTS.md) - Level 0-1 테스트 결과 (40 tests passing)
- [API Corrections](API_CORRECTIONS.md) - API 사용법 및 올바른 예제
- [Testing Plan](TESTING_PLAN.md) - 체계적 테스트 전략
- [Architecture](ARCHITECTURE.md) - 시스템 아키텍처 상세
- [Examples](examples/) - 검증된 예제 코드
  - [00_basic_parameters_corrected.py](examples/00_basic_parameters_corrected.py) - 파라미터 시스템 완전 가이드

---

## 🧩 예제

### 1. 파라미터 시스템 사용

```python
from koocad.core.parameters import FloatParameter, ExpressionParameter, ParameterSet
from koocad.core.expressions import ExpressionEngine

# 파라미터 생성 (키워드 인자 필수)
width = FloatParameter(name='width', value=10.0, min_value=0.0, max_value=100.0)
height = FloatParameter(name='height', value=20.0, min_value=0.0, max_value=100.0)
area = ExpressionParameter(name='area', value='width * height')

# ParameterSet으로 의존성 관리
params = ParameterSet()
params.add(width)
params.add(height)
params.add(area)

# 모든 파라미터 평가 (의존성 자동 해결)
values = params.evaluate_all()  # {'width': 10.0, 'height': 20.0, 'area': 200.0}
```

### 2. 프리셋 라이브러리 사용

```python
from koocad.core.presets import BGAPresets, MLCCPresets, PresetLibrary

# BGA 표준 프리셋 (JEDEC)
bga_15x15 = BGAPresets.get_all()['BGA_15x15_0.8mm']
values = bga_15x15.evaluate_all()
# {'ball_rows': 15, 'ball_cols': 15, 'ball_pitch': 0.8, ...}

# MLCC 표준 프리셋 (EIA)
mlcc_0603 = MLCCPresets.get_all()['MLCC_0603']
# EIA 0603: 1.6mm x 0.8mm x 0.8mm

# 통합 라이브러리
library = PresetLibrary()
all_presets = library.list_presets()  # 21 presets (7 BGA + 8 MLCC + 6 RES)
```

### 노드 그래프 (Python API)

```python
from koocad.ui.nodes import NodeGraph, BoxNode, FilletNode, ExportNode

graph = NodeGraph()

# Create nodes
box = BoxNode(width=10, height=10, depth=5)
fillet = FilletNode(radius=0.5)
export = ExportNode(format="step")

# Connect
graph.connect(box.output, fillet.input)
graph.connect(fillet.output, export.input)

# Execute
graph.execute()
```

### 배치 파라미터 스윕 (HPC)

```yaml
# sweep_config.yaml
sweep_type: cartesian
parameters:
  bga_size: [10, 12, 14, 16]
  ball_pitch: [0.5, 0.65, 0.8]
  substrate_thickness: [0.6, 0.8, 1.0]

output_formats: [step, stl, dyna]
mesh_quality: high
```

```bash
# Submit Slurm job array
koocad batch submit \
  --config sweep_config.yaml \
  --output-dir /scratch/results \
  --array 0-47
```

---

## 🗺️ Roadmap

**현재 상태**: Phase 145/145 완료 ✅ | [테스트 결과](TEST_RESULTS.md) | [Master Plan](MASTER_PLAN.md)

### ✅ Phase 1-35: Core Infrastructure (완료)
- [x] Project structure & configuration
- [x] Parameter system with Pydantic
- [x] Expression engine with SymPy
- [x] Validation & serialization
- [x] Industry-standard presets (JEDEC, EIA)
- [x] **40 unit tests passing** ✅

### ✅ Phase 36-85: CAD Kernels & Components (완료)
- [x] CadQuery wrapper implementation
- [x] Shape abstraction layer
- [x] BGA/WLP generators
- [x] MLCC/Resistor/Inductor generators
- [x] Connector generators

### ✅ Phase 86-105: Frontend UI (완료)
- [x] DearPyGui node editor
- [x] Graph executor with topological sort
- [x] 3D preview integration
- [x] Parameter inspector

### ✅ Phase 106-120: Backend API (완료)
- [x] FastAPI server with JWT authentication
- [x] PostgreSQL + SQLAlchemy ORM
- [x] Celery job queue + Redis
- [x] WebSocket real-time updates
- [x] Prometheus metrics & rate limiting

### ✅ Phase 121-135: Export & Meshing (완료)
- [x] STEP/IGES/STL/GLB/OBJ exporters
- [x] Gmsh mesher integration
- [x] LS-DYNA keyword generator
- [x] Mesh quality checker

### ✅ Phase 136-145: HPC Integration (완료)
- [x] Slurm job script generator
- [x] Parameter sweep (Cartesian, Sobol, LHS)
- [x] Apptainer container builder
- [x] Job monitoring & result aggregation

**다음 단계**: CadQuery 설치 → Level 2 테스트 (실제 CAD 생성)

---

## 🤝 Contributing

기여를 환영합니다! 다음을 참고해주세요:

1. [Contributing Guide](CONTRIBUTING.md)
2. [Code of Conduct](CODE_OF_CONDUCT.md)
3. [Development Setup](docs/development.md)

---

## 📄 License

MIT License - 자세한 내용은 [LICENSE](LICENSE) 참조

---

## 🙏 Acknowledgments

- [CadQuery](https://github.com/CadQuery/cadquery) - Python CAD 라이브러리
- [OpenCASCADE](https://www.opencascade.com/) - 핵심 CAD kernel
- [DearPyGui](https://github.com/hoffstadt/DearPyGui) - GPU 가속 Python GUI
- [FastAPI](https://fastapi.tiangolo.com/) - 현대적 Python 웹 프레임워크

---

## 📧 Contact

- 프로젝트 홈페이지: [https://koocad.com](https://koocad.com)
- 이슈 트래커: [GitHub Issues](https://github.com/yourusername/KooCADImGUI/issues)
- 이메일: dev@koocad.com

---

<div align="center">

Made with ❤️ by KooCAD Team

</div>
