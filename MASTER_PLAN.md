# KooCAD Parametric System - Master Plan (145 Phases)

## 프로젝트 개요

**목표**: 파라메트릭 전자부품 CAD 자동화 시스템
**주요 사용 사례**: BGA/WLP 패키지, 수동소자(캐패시터, 코일), 커넥터, IC 등
**핵심 기능**: 완전 파라메트릭 모델링, 노드 기반 워크플로우, HPC 배치 생성, FEA 메싱 파이프라인

---

## 아키텍처 스택

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend: DearPyGui (Node Editor + Parameter Controls)     │
├─────────────────────────────────────────────────────────────┤
│  Orchestrator: FastAPI (REST + WebSocket)                   │
├─────────────────────────────────────────────────────────────┤
│  CAD Kernel A: CadQuery (Python - General Features)         │
│  CAD Kernel B: OCCT C++ (pybind11 - Complex/Batch)          │
├─────────────────────────────────────────────────────────────┤
│  Export Layer: STEP/IGES/STL/GLB + Mesh (Gmsh/Netgen)       │
│  FEA Pipeline: LS-DYNA Keyword Generator                     │
├─────────────────────────────────────────────────────────────┤
│  Batch System: Slurm + Apptainer (JSON Parameter Sweep)     │
├─────────────────────────────────────────────────────────────┤
│  Data Lake: PostgreSQL + MinIO (Metadata + Binary Storage)  │
└─────────────────────────────────────────────────────────────┘
```

---

## Domain 1: 프로젝트 초기화 & 개발 인프라 (Phase 1-15)

### Phase 1: 프로젝트 구조 생성
- 모노레포 구조 설계 (frontend, backend, kernels, libs, examples)
- pyproject.toml, setup.py 설정 (Poetry/PDM 사용)
- .gitignore, .editorconfig, pre-commit hooks

### Phase 2: 개발 환경 Docker 구성
- Dockerfile.dev (Python 3.11 + OCCT + CadQuery)
- docker-compose.yml (FastAPI + PostgreSQL + MinIO + Redis)
- VSCode devcontainer.json

### Phase 3: CI/CD 파이프라인 기초
- GitHub Actions: lint (ruff, mypy)
- GitHub Actions: test (pytest)
- GitHub Actions: build Docker images

### Phase 4: 문서화 인프라
- Sphinx + Read the Docs 설정
- API 문서 자동 생성 (FastAPI OpenAPI)
- 마크다운 기반 사용자 가이드 구조

### Phase 5: 코드 품질 도구
- pre-commit: black, isort, ruff, mypy
- pytest-cov (코드 커버리지 80%+ 목표)
- bandit (보안 취약점 검사)

### Phase 6: 로깅 & 모니터링 인프라
- structlog 설정 (JSON 로그)
- OpenTelemetry 통합 (traces, metrics)
- Prometheus + Grafana 대시보드 템플릿

### Phase 7: 버전 관리 전략
- Semantic Versioning 정책
- Changelog 자동 생성 (conventional commits)
- Git branch 전략 (main, develop, feature/*)

### Phase 8: 테스트 데이터 생성 도구
- Faker 기반 파라미터 생성기
- Golden test 데이터셋 (BGA 샘플 10종)
- Regression test 자동화

### Phase 9: 성능 벤치마크 프레임워크
- pytest-benchmark 설정
- CAD 생성 시간 측정 (단위: ms)
- 메모리 프로파일링 (memory_profiler)

### Phase 10: 보안 & 시크릿 관리
- python-dotenv (.env 파일)
- Vault 통합 (프로덕션 환경)
- API Key 로테이션 정책

### Phase 11: 멀티플랫폼 빌드
- Linux (Ubuntu 22.04, RHEL 8)
- Windows (MinGW-w64 + MSVC)
- macOS (Apple Silicon + Intel)

### Phase 12: 패키지 배포 인프라
- PyPI private repository
- Conda-forge 채널
- Docker Hub / GHCR 이미지

### Phase 13: 개발자 도구 CLI
- Click 기반 `koocad` 명령어
- 프로젝트 생성 스캐폴딩
- 플러그인 템플릿 생성

### Phase 14: 라이선스 & 의존성 관리
- SPDX 라이선스 헤더 자동 추가
- pip-audit (의존성 취약점 검사)
- 라이선스 호환성 검증

### Phase 15: 온보딩 문서 & 예제
- CONTRIBUTING.md
- 개발자 온보딩 가이드
- "Hello World" CAD 예제 (Simple Box)

---

## Domain 2: 핵심 데이터 모델 & 파라메트릭 엔진 (Phase 16-30)

### Phase 16: 파라메트릭 타입 시스템
- Parameter Base Class (float, int, bool, str, enum)
- Constraint 시스템 (min, max, step, validator)
- Unit 시스템 (mm, inch, mil 변환)

### Phase 17: Expression Engine
- sympy 기반 수식 파서
- 변수 간 의존성 그래프 (DAG)
- Circular dependency 감지

### Phase 18: Parameter Group & Hierarchy
- ParameterGroup (논리적 그룹핑)
- Nested parameters (BGA.substrate.thickness)
- Inheritance (템플릿 파라미터 상속)

### Phase 19: Schema 정의 시스템
- Pydantic BaseModel 기반
- JSON Schema 자동 생성
- Schema 마이그레이션 도구

### Phase 20: 파라메트릭 인스턴스 관리
- ParameterSet (불변 스냅샷)
- Diff 알고리즘 (변경사항 추적)
- Merge 전략 (충돌 해결)

### Phase 21: 제약 조건 솔버
- Constraint Satisfaction Problem (CSP)
- 불가능한 조합 조기 검증
- 대안 제안 엔진

### Phase 22: 파라미터 프리셋 시스템
- 산업 표준 프리셋 (JEDEC, IPC)
- 사용자 커스텀 프리셋
- 프리셋 Import/Export (JSON/YAML)

### Phase 23: 파라미터 검증 프레임워크
- Validator 체인 (순차 검증)
- Async 검증 (외부 API 호출)
- 검증 에러 다국어 메시지

### Phase 24: 히스토리 & Undo/Redo
- Command Pattern 구현
- History Stack (최대 100 steps)
- Branching history (실험적 변경)

### Phase 25: 파라메트릭 테스트 유틸리티
- Hypothesis 기반 Property Testing
- Fuzzing (invalid parameter ranges)
- Metamorphic testing

### Phase 26: 파라미터 시리얼라이제이션
- JSON (human-readable)
- MessagePack (binary, compact)
- Protocol Buffers (gRPC 통신)

### Phase 27: 파라미터 암호화
- 민감한 파라미터 암호화 (Fernet)
- Access Control List (ACL)
- Audit Log (누가 언제 변경했는지)

### Phase 28: 파라미터 메타데이터
- 설명, 단위, 태그
- 검색 인덱스 (Elasticsearch)
- 자동 문서 생성

### Phase 29: Dynamic Parameter Discovery
- 런타임에 파라미터 추가
- Plugin에서 새 파라미터 등록
- Hot-reload (서버 재시작 없이)

### Phase 30: 파라메트릭 IDE 유틸리티
- Parameter Inspector (디버깅)
- Dependency Visualizer (그래프)
- Performance Profiler (느린 expression 찾기)

---

## Domain 3: CAD Kernel 통합 & Geometry Core (Phase 31-50)

### Phase 31: CadQuery Wrapper Layer
- Workplane abstraction
- Operation chaining (fluent API)
- Error handling (OCCT exceptions)

### Phase 32: OCCT C++ Core Module
- pybind11 binding 생성
- 핵심 OCCT 클래스 (TopoDS_Shape, BRep)
- Memory management (RAII)

### Phase 33: Shape 추상화 레이어
- KooShape (CadQuery + OCCT 통합)
- 자동 변환 (CQ ↔ OCCT)
- Type hints (Generic[ShapeType])

### Phase 34: Boolean Operations
- Union, Intersect, Subtract
- Batch boolean (여러 객체 병합)
- Fuzzy boolean (tolerance 제어)

### Phase 35: Fillet & Chamfer Engine
- Variable radius fillet
- Edge 선택 알고리즘
- Performance 최적화 (병렬 처리)

### Phase 36: Sweep & Loft Operations
- Path-based sweep
- Multi-section loft
- Twist angle 제어

### Phase 37: Pattern & Array
- Linear pattern (1D, 2D)
- Circular pattern
- Custom path pattern

### Phase 38: Shell & Offset
- Constant offset
- Variable offset (tapered walls)
- Inside/outside offset

### Phase 39: Draft Angle
- 사출성형 draft angle
- Face 선택 전략
- Neutral plane 설정

### Phase 40: 곡면 생성 엔진
- NURBS surface
- Bézier patch
- Coons patch

### Phase 41: 메시 생성 (테셀레이션)
- Adaptive tessellation
- Quality metric (aspect ratio)
- STL binary/ASCII

### Phase 42: 기하학 분석 도구
- Volume, Surface area 계산
- Center of mass
- Moment of inertia

### Phase 43: 충돌 감지
- Bounding box check (broad phase)
- Precise intersection (narrow phase)
- Clearance 계산

### Phase 44: Topology 유틸리티
- Face, Edge, Vertex 탐색
- Adjacent element 찾기
- Orientation 정규화

### Phase 45: 변환 매트릭스
- Translation, Rotation, Scale
- Mirror
- Compound transform

### Phase 46: Import/Export 기본
- STEP (AP203, AP214)
- IGES (5.3)
- BREP (OCCT native)

### Phase 47: STL Export 최적화
- Quad-dominant meshing
- Normal smoothing
- File size 압축

### Phase 48: GLB/glTF Export
- PBR materials
- Animation (폭발도)
- Binary packing

### Phase 49: 2D Drawing Export
- DXF (AutoCAD R2018)
- SVG (웹 프리뷰)
- PDF (도면 문서)

### Phase 50: Geometry Validation
- Self-intersection 검사
- Invalid topology 복구
- Simplify (중복 제거)

---

## Domain 4: 전자부품 형상 라이브러리 (Phase 51-70)

### Phase 51: 패키지 베이스 클래스
- Package (abstract)
- FootprintGenerator (2D)
- Body3DGenerator (3D)

### Phase 52: 기본 IC 패키지 - DIP
- Through-hole pins
- Notch/dot 마커
- Parameter: pin_count, pitch, body_width

### Phase 53: 기본 IC 패키지 - SOIC
- Gull-wing leads
- Lead forming
- Parameter: lead_span, lead_width

### Phase 54: 기본 IC 패키지 - QFP/LQFP
- 4면 lead 배치
- Corner chamfer
- Parameter: pin_count, pitch, package_size

### Phase 55: 고급 패키지 - QFN/DFN
- Exposed pad (thermal pad)
- Side wettable flanks
- Parameter: pad_size, pad_rows

### Phase 56: BGA 기본 구조
- Substrate (multilayer)
- Solder ball array
- Parameter: ball_pitch, ball_diameter, array_size

### Phase 57: BGA Ball Map Generator
- Full array, peripheral array
- Custom pattern (missing balls)
- JSON ball map import

### Phase 58: BGA Underfill Simulation Geometry
- Corner fillets
- Capillary gap
- Air pocket modeling

### Phase 59: WLP (Wafer Level Package)
- Redistribution layer (RDL)
- Passivation opening
- Bump array

### Phase 60: 적층 세라믹 캐패시터 (MLCC)
- Dielectric layers (100+ layers)
- Internal electrodes (interdigitated)
- Termination (end caps)

### Phase 61: Chip Resistor
- Thick film resistor element
- Protective coating
- Laser trim pattern

### Phase 62: Inductor (Chip Type)
- Coil winding (parametric)
- Ferrite core
- Magnetic shield

### Phase 63: Power Inductor (Toroid)
- Torus geometry
- Wire winding path
- Lead-out pins

### Phase 64: Connector - Pin Header
- 2.54mm pitch array
- Plastic housing
- Pin plating

### Phase 65: Connector - Board-to-Board
- Mating interface
- Alignment features
- Contact spring

### Phase 66: Crystal Oscillator
- Quartz blank
- Metal electrodes
- Ceramic package

### Phase 67: LED Package
- Reflector cup
- Die attach pad
- Lens (dome/flat)

### Phase 68: Fuse (Surface Mount)
- Fuse element (serpentine)
- Arc-quenching chamber
- Blow indicator

### Phase 69: Heat Sink
- Fin array (parametric)
- Thermal via pattern
- Mounting holes

### Phase 70: Thermal Pad Generator
- Via-in-pad
- Thermal relief
- Solder mask opening

---

## Domain 5: 고급 BGA/WLP 전문 시스템 (Phase 71-85)

### Phase 71: BGA Substrate 멀티레이어
- Layer stack-up definition
- Via (blind, buried, through)
- Copper thickness profile

### Phase 72: BGA Trace Routing (Parametric)
- Fan-out pattern
- Escape routing
- Impedance control (width/spacing)

### Phase 73: BGA Solder Mask
- Dam between pads
- NSMD vs. SMD
- Color/finish

### Phase 74: BGA Die Attach
- Die paddle
- Adhesive fillet
- Wirebond pad

### Phase 75: Wirebond Geometry
- Wire arc (catenary curve)
- Loop height
- Bond pad clearance

### Phase 76: Flip Chip Bumping
- C4 bump (solder)
- Copper pillar
- Micro-bump (TSV)

### Phase 77: Package Warpage Simulation Prep
- Neutral axis calculation
- Material property assignment
- Thermal load definition

### Phase 78: Mold Compound Geometry
- Overmold shape
- Parting line
- Gate location

### Phase 79: Package Marking
- Laser marking area
- 2D barcode (DataMatrix)
- Orientation marker

### Phase 80: Advanced Ball Map Editor (GUI)
- Visual grid editor
- Import from Excel/CSV
- JEDEC standard presets

### Phase 81: WLP RDL Generator
- Multi-layer RDL
- Via stacking
- UBM (Under Bump Metallization)

### Phase 82: Fan-Out WLP (FOWLP)
- Reconstitution
- Oversize substrate
- Edge trim line

### Phase 83: 2.5D/3D Integration
- Interposer
- TSV (Through Silicon Via)
- Die stacking

### Phase 84: Package-on-Package (PoP)
- Top package ball map
- Bottom package pad map
- Stacking height

### Phase 85: Advanced Thermal Analysis Prep
- Thermal via array generation
- Heat spreader geometry
- TIM (Thermal Interface Material) layer

---

## Domain 6: Frontend - DearPyGui Node Editor (Phase 86-100)

### Phase 86: DearPyGui 기본 설정
- Window 생성
- Theme (dark/light)
- Font (Korean 지원)

### Phase 87: Node Editor 초기화
- dpg.add_node_editor()
- Grid 설정
- Zoom/pan controls

### Phase 88: Node Base Class
- Input/Output pins
- Title bar
- Resize handle

### Phase 89: Parameter Input Nodes
- Float slider node
- Int input node
- Enum dropdown node

### Phase 90: Geometry Operation Nodes
- Box node
- Cylinder node
- Boolean union node

### Phase 91: 전자부품 Template Nodes
- BGA node
- Capacitor node
- Connector node

### Phase 92: Link (Edge) 시스템
- Pin 연결/해제
- Type checking (data validation)
- Link color (data type 표시)

### Phase 93: Node Graph Execution Engine
- Topological sort (실행 순서)
- Caching (중간 결과)
- Error propagation

### Phase 94: 3D Viewport 통합
- OpenGL/Vulkan context
- Camera controls (orbit, pan, zoom)
- Render loop

### Phase 95: 3D Model Rendering
- Mesh upload (VBO/IBO)
- Shader (Phong shading)
- Wireframe overlay

### Phase 96: Material Editor
- PBR material parameters
- Texture mapping
- Material library

### Phase 97: Property Panel
- Selected node properties
- Live update (reactive)
- Undo/redo

### Phase 98: Toolbar & Menu
- File (New, Open, Save, Export)
- Edit (Undo, Redo, Copy, Paste)
- View (Reset Camera, Grid, Axes)

### Phase 99: Keyboard Shortcuts
- Ctrl+Z/Y (Undo/Redo)
- Ctrl+C/V (Copy/Paste)
- Delete (노드 삭제)

### Phase 100: Node Search/Palette
- Fuzzy search
- Category tree
- Recent nodes

### Phase 101: Node Graph Templates
- 저장/불러오기
- Template gallery
- Version control (git integration)

### Phase 102: Multi-tab Editor
- Tab bar
- Unsaved changes indicator
- Split view

### Phase 103: Console/Log Panel
- Error messages
- Warning highlights
- Log filtering

### Phase 104: Progress Indicator
- Long-running operation (CAD gen)
- Progress bar
- Cancel button

### Phase 105: Node Animation
- Parameter sweep preview
- Timeline scrubbing
- Keyframe editor

---

## Domain 7: Orchestrator - FastAPI 백엔드 (Phase 106-120)

### Phase 106: FastAPI 프로젝트 구조
- app/ (routers, models, services)
- SQLAlchemy models
- Alembic migrations

### Phase 107: RESTful API 설계
- /api/v1/parameters (CRUD)
- /api/v1/jobs (CAD 생성 작업)
- /api/v1/exports (파일 다운로드)

### Phase 108: WebSocket 실시간 통신
- Job progress update
- 3D preview streaming
- Error notification

### Phase 109: 인증 & 인가
- JWT token
- Role-based access (admin, user, guest)
- API key (batch 작업)

### Phase 110: Job Queue (Celery)
- Redis broker
- Worker pool (4+ workers)
- Task routing (priority)

### Phase 111: CAD 생성 Task
- Parameter validation
- Kernel 선택 (CadQuery vs. OCCT)
- Result caching

### Phase 112: Export Task
- STEP/STL 변환
- Zip archive (multi-file)
- Cloud storage upload (MinIO)

### Phase 113: Database Models
- Project, Job, ParameterSet
- Relationship (one-to-many)
- Index (query optimization)

### Phase 114: API Rate Limiting
- Per-user quota
- Burst limit
- 429 response

### Phase 115: API Documentation
- OpenAPI 3.0 spec
- Swagger UI
- ReDoc

### Phase 116: Health Check Endpoint
- /health (liveness)
- /ready (readiness)
- Dependency status (DB, Redis)

### Phase 117: Metrics Collection
- Prometheus exporter
- Request duration histogram
- Error rate counter

### Phase 118: Background Job Monitoring
- Flower (Celery UI)
- Job retry logic
- Dead letter queue

### Phase 119: API Versioning
- URL prefix (/api/v1, /api/v2)
- Deprecation warning
- Migration guide

### Phase 120: GraphQL API (선택)
- Strawberry
- Schema stitching
- DataLoader (N+1 방지)

---

## Domain 8: Export & 메싱 파이프라인 (Phase 121-135)

### Phase 121: STEP Export (AP214)
- Assembly structure
- Color/material
- Metadata (title, author)

### Phase 122: IGES Export
- Entity type 선택
- BREP vs. CSG
- Precision control

### Phase 123: STL Export (Binary)
- Triangle count 최적화
- Normal vector 계산
- File size 압축

### Phase 124: GLB/glTF 2.0 Export
- Scene graph
- PBR materials (metallic-roughness)
- Animation (exploded view)

### Phase 125: OBJ/MTL Export
- UV mapping
- Texture coordinates
- Material library

### Phase 126: Gmsh 메싱
- Python API (gmsh-sdk)
- Mesh size field
- Element type (Tet10, Hex8)

### Phase 127: Netgen 메싱
- NGSolve integration
- Boundary layer mesh
- Anisotropic refinement

### Phase 128: LS-DYNA Keyword Generator
- *NODE, *ELEMENT
- *PART, *SECTION
- *MAT (material card)

### Phase 129: LS-DYNA Contact Definition
- Automatic contact
- Tiebreak contact
- Friction coefficient

### Phase 130: LS-DYNA Load & BC
- *LOAD_NODE_SET
- *BOUNDARY_SPS
- *INITIAL_VELOCITY

### Phase 131: Mesh Quality Check
- Aspect ratio
- Jacobian
- Warpage

### Phase 132: Mesh Refinement
- Adaptive refinement (stress)
- Local refinement (feature)
- Coarsening (far-field)

### Phase 133: Mesh Conversion
- Gmsh → LS-DYNA
- Netgen → Abaqus
- Universal format (UNV)

### Phase 134: Mesh Visualization
- VTK export
- ParaView integration
- Web viewer (vtk.js)

### Phase 135: Mesh Metadata
- Element count
- Node count
- Mesh time

---

## Domain 9: Batch 시스템 & HPC 통합 (Phase 136-145)

### Phase 136: Slurm Job Script Generator
- sbatch template
- Resource request (CPU, mem)
- Time limit

### Phase 137: Parameter Sweep JSON
- Cartesian product
- Random sampling (DoE)
- Sobol sequence (QMC)

### Phase 138: Apptainer 컨테이너
- Definition file (.def)
- Bind mount (/data, /scratch)
- GPU support

### Phase 139: Job Array
- Array index ($SLURM_ARRAY_TASK_ID)
- Parameter mapping
- Output directory

### Phase 140: Job Dependency
- afterok, afterany
- Chain jobs (preprocess → solve → postprocess)
- Failure handling

### Phase 141: Checkpoint/Restart
- State serialization
- Resume from failure
- Incremental progress

### Phase 142: Result Aggregation
- Collect output files
- Summary statistics
- Plot generation (matplotlib)

### Phase 143: HPC Monitoring Dashboard
- Grafana dashboard
- Job queue status
- Resource utilization

### Phase 144: Cost Tracking
- CPU-hour accounting
- Storage quota
- Report generation

### Phase 145: Burst to Cloud (선택)
- AWS Batch
- Azure CycleCloud
- Google Cloud Batch

---

## Appendix: 추가 고려사항

### A. 보안
- Input sanitization (SQL injection, XSS)
- Secrets management (Vault)
- Audit logging

### B. 확장성
- Horizontal scaling (Kubernetes)
- Caching (Redis, Memcached)
- CDN (static assets)

### C. 국제화
- i18n (gettext)
- 다국어 UI (한국어, 영어, 중국어)
- Date/time locale

### D. 접근성
- WCAG 2.1 AA
- Keyboard navigation
- Screen reader 지원

### E. 플러그인 시스템
- Plugin API
- Hot-reload
- Marketplace

---

## 실행 우선순위

**Critical Path (6개월)**:
- Domain 1, 2, 3 (인프라 + 핵심 엔진)
- Domain 4 (전자부품 라이브러리 기본)
- Domain 6 (UI 기본)
- Domain 7 (API 기본)

**Phase 2 (6-12개월)**:
- Domain 5 (BGA/WLP 전문)
- Domain 8 (Export + 메싱)
- Domain 9 (Batch 시스템)

**Phase 3 (12-18개월)**:
- 고급 기능, 최적화, 문서화
- 프로덕션 배포
- 커뮤니티 빌딩

---

**작성일**: 2025-11-10
**버전**: 1.0.0
**작성자**: Claude AI + Human Collaborator
