# KooCAD - Parametric Electronic Component CAD System

<div align="center">

![KooCAD Logo](docs/images/logo.png)

**완전 파라메트릭 전자부품 CAD 자동화 플랫폼**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

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

- Python 3.11+
- Docker & Docker Compose
- (Optional) CUDA 11.8+ for GPU rendering

### 설치

```bash
# 1. Clone repository
git clone https://github.com/yourusername/KooCADImGUI.git
cd KooCADImGUI

# 2. Install with all dependencies
pip install -e ".[all]"

# 3. Start infrastructure (DB, Redis, MinIO)
docker-compose up -d

# 4. Run database migrations
alembic upgrade head

# 5. Start API server
koocad-server --host 0.0.0.0 --port 8000

# 6. (별도 터미널) Start UI
koocad-ui
```

### 첫 번째 CAD 생성

```python
from koocad.components.bga import BGAGenerator
from koocad.core.parameters import ParameterSet

# BGA 파라미터 정의
params = ParameterSet({
    "substrate_width": 12.0,   # mm
    "substrate_height": 12.0,
    "substrate_thickness": 0.8,
    "ball_pitch": 0.8,
    "ball_diameter": 0.4,
    "ball_rows": 15,
    "ball_cols": 15,
})

# CAD 생성
generator = BGAGenerator()
shape = generator.generate(params)

# Export
shape.export_step("my_bga.step")
shape.export_stl("my_bga.stl")
```

---

## 📚 문서

- [Master Plan](MASTER_PLAN.md) - 145 Phase 전체 계획
- [Architecture](ARCHITECTURE.md) - 시스템 아키텍처 상세
- [API Reference](docs/api/) - REST API 문서
- [Component Library](docs/components/) - 전자부품 라이브러리
- [Tutorial](docs/tutorial/) - 단계별 튜토리얼

---

## 🧩 예제

### BGA 패키지 생성

```python
from koocad.components.bga import BGAPackage

bga = BGAPackage(
    size=(12, 12),
    ball_pitch=0.8,
    ball_pattern="peripheral",  # or "full"
)

bga.export("output.step")
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

현재 상태: **Phase 0 (Planning)**

### Phase 1: Core Infrastructure (1-2개월)
- [x] Project structure
- [ ] CI/CD pipeline
- [ ] Docker environment
- [ ] Parameter engine

### Phase 2: CAD Kernels (2-3개월)
- [ ] CadQuery wrapper
- [ ] OCCT C++ module
- [ ] Basic shapes library

### Phase 3: Component Library (3-4개월)
- [ ] BGA generator
- [ ] MLCC generator
- [ ] Inductor generator

### Phase 4: Frontend UI (4-5개월)
- [ ] DearPyGui node editor
- [ ] 3D viewport
- [ ] Property panel

### Phase 5: Backend API (5-6개월)
- [ ] FastAPI server
- [ ] Job queue (Celery)
- [ ] Data lake

상세 일정: [MASTER_PLAN.md](MASTER_PLAN.md)

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
