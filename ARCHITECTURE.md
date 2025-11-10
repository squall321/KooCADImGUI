# KooCAD System Architecture

## 시스템 개요

KooCAD는 **완전 파라메트릭** 전자부품 CAD 자동화 플랫폼으로, 노드 기반 워크플로우와 HPC 배치 생성을 지원합니다.

---

## 레이어 아키텍처

```
┌──────────────────────────────────────────────────────────────────┐
│                    Presentation Layer                             │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐     │
│  │ DearPyGui UI   │  │ Web Dashboard  │  │  CLI Tools     │     │
│  │ (Node Editor)  │  │ (React/Vue)    │  │  (Click)       │     │
│  └────────────────┘  └────────────────┘  └────────────────┘     │
└──────────────────────────────────────────────────────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                      API Gateway Layer                            │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  FastAPI Server (Uvicorn + Gunicorn)                       │  │
│  │  - REST API (/api/v1/*)                                    │  │
│  │  - WebSocket (/ws/*)                                       │  │
│  │  - GraphQL (optional)                                      │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                     Business Logic Layer                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐  │
│  │ Parameter Engine │  │  Job Orchestrator│  │ Export Manager│  │
│  │ - Validation     │  │  - Celery Queue  │  │ - STEP/IGES   │  │
│  │ - Expression Eval│  │  - Priority      │  │ - STL/GLB     │  │
│  │ - Constraint Solver│ │  - Retry Logic   │  │ - Mesh Gen    │  │
│  └──────────────────┘  └──────────────────┘  └───────────────┘  │
└──────────────────────────────────────────────────────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                       CAD Kernel Layer                            │
│  ┌─────────────────────┐        ┌──────────────────────┐         │
│  │  CadQuery Engine    │   ←→   │  OCCT C++ Module     │         │
│  │  (Python)           │        │  (pybind11 binding)  │         │
│  │  - Fluent API       │        │  - BRep operations   │         │
│  │  - High-level ops   │        │  - Batch processing  │         │
│  └─────────────────────┘        └──────────────────────┘         │
│             ▼                              ▼                      │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │           OpenCASCADE Technology (OCCT)                  │    │
│  │  - Topology (BRep_Tool, TopoDS)                          │    │
│  │  - Geometry (Geom_Surface, Geom_Curve)                   │    │
│  │  - Modeling (BRepBuilderAPI, BRepFilletAPI)              │    │
│  └──────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Component Library Layer                        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐             │
│  │ BGA/WLP      │ │ Passives     │ │ Connectors   │             │
│  │ - Substrate  │ │ - MLCC       │ │ - Pin Header │             │
│  │ - Ball Map   │ │ - Inductor   │ │ - BTB        │             │
│  │ - RDL        │ │ - Resistor   │ │ - FPC        │             │
│  └──────────────┘ └──────────────┘ └──────────────┘             │
└──────────────────────────────────────────────────────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Data Persistence Layer                         │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐  │
│  │ PostgreSQL       │  │ MinIO (S3)       │  │ Redis         │  │
│  │ - Metadata       │  │ - STEP files     │  │ - Cache       │  │
│  │ - Parameters     │  │ - STL meshes     │  │ - Queue       │  │
│  │ - Job history    │  │ - Screenshots    │  │ - Sessions    │  │
│  └──────────────────┘  └──────────────────┘  └───────────────┘  │
└──────────────────────────────────────────────────────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                      HPC Integration Layer                        │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Slurm Cluster                                             │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │  │
│  │  │ Login Node   │  │ Compute Node │  │ GPU Node     │    │  │
│  │  │ - Submit Job │  │ - Apptainer  │  │ - Rendering  │    │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘    │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 주요 컴포넌트 상세

### 1. Parameter Engine

**책임**:
- 파라미터 타입 정의 (float, int, enum, expression)
- 제약 조건 검증 (min, max, dependencies)
- Expression 평가 (sympy)
- 단위 변환 (mm ↔ inch ↔ mil)

**핵심 클래스**:
```python
class Parameter(ABC):
    name: str
    value: Any
    unit: Unit
    constraints: List[Constraint]

class FloatParameter(Parameter):
    min_value: float
    max_value: float
    step: float

class ExpressionParameter(Parameter):
    expression: str  # e.g., "substrate_thickness * 0.8"
    dependencies: List[str]
```

**의존성**:
- sympy (expression parsing)
- pydantic (validation)
- pint (unit conversion)

---

### 2. CAD Kernel Abstraction

**인터페이스**:
```python
class ICADKernel(ABC):
    @abstractmethod
    def create_box(self, width, height, depth) -> Shape: ...

    @abstractmethod
    def boolean_union(self, shapes: List[Shape]) -> Shape: ...

    @abstractmethod
    def export_step(self, shape: Shape, path: str): ...
```

**구현체**:
- `CadQueryKernel`: 일반 사용 (빠른 프로토타입)
- `OCCTKernel`: 복잡/대량 처리 (C++ 성능)

**자동 선택 로직**:
- Shape count < 100 → CadQuery
- Shape count ≥ 100 → OCCT
- Boolean ops > 50 → OCCT
- User override: `kernel="occt"`

---

### 3. BGA Generator (상세 예제)

**파라미터 구조**:
```yaml
bga:
  substrate:
    width: 12.0  # mm
    height: 12.0  # mm
    thickness: 0.8  # mm
    layer_count: 4

  ball_map:
    pitch: 0.8  # mm
    diameter: 0.4  # mm
    pattern: "full"  # full, peripheral, custom
    rows: 15
    cols: 15
    missing_balls: [[0, 0], [14, 14]]  # corner balls removed

  soldermask:
    color: "green"
    finish: "NSMD"  # Non-Solder Mask Defined
    opening_offset: 0.05  # mm

  marking:
    text: "KOOCAD BGA"
    font_size: 1.0
    position: [6.0, 6.0]
```

**생성 알고리즘**:
1. Substrate body 생성 (chamfer 모서리)
2. Layer stack 추가 (copper, dielectric)
3. Ball array 생성 (pattern에 따라)
4. Soldermask opening 추가
5. Marking 영역 음각
6. Assembly로 병합

**성능**:
- 15×15 BGA: ~200ms (CadQuery)
- 40×40 BGA: ~800ms (OCCT)

---

### 4. Node Graph Executor

**실행 모델**:
```python
class NodeGraph:
    nodes: Dict[str, Node]
    edges: List[Edge]

    def execute(self) -> Dict[str, Any]:
        # 1. Topological sort
        sorted_nodes = self._topological_sort()

        # 2. Execute in order
        cache = {}
        for node in sorted_nodes:
            inputs = self._get_inputs(node, cache)
            output = node.execute(inputs)
            cache[node.id] = output

        return cache
```

**노드 타입**:
- **Input Nodes**: ParameterNode, FileNode
- **Operation Nodes**: BoxNode, BooleanNode, FilletNode
- **Component Nodes**: BGANode, CapacitorNode
- **Output Nodes**: ExportNode, ViewNode

**최적화**:
- Caching: 입력 불변 시 재실행 안 함
- Parallel: 독립적인 branch 병렬 실행
- Lazy: 필요한 노드만 실행

---

### 5. Export Pipeline

**STEP Export (상세)**:
```python
def export_step(shape: Shape, path: str, metadata: Dict):
    # 1. Shape validation
    if not shape.isValid():
        shape = fix_shape(shape)

    # 2. Create STEP writer
    writer = STEPControl_Writer()

    # 3. Set metadata (AP214)
    writer.Model().SetNameField("product_name", metadata["name"])
    writer.Model().SetAuthorField(metadata["author"])

    # 4. Transfer shape
    writer.Transfer(shape._wrapped, STEPControl_AsIs)

    # 5. Write file
    writer.Write(path)
```

**GLB Export (PBR)**:
```python
def export_glb(shape: Shape, path: str, material: PBRMaterial):
    # 1. Tessellation
    mesh = tessellate(shape, quality=0.5)

    # 2. Create glTF scene
    gltf = {
        "asset": {"version": "2.0"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [{
            "primitives": [{
                "attributes": {"POSITION": 0, "NORMAL": 1},
                "material": 0
            }]
        }],
        "materials": [{
            "pbrMetallicRoughness": {
                "baseColorFactor": material.base_color,
                "metallicFactor": material.metallic,
                "roughnessFactor": material.roughness
            }
        }]
    }

    # 3. Pack binary buffers
    # 4. Write GLB
```

---

### 6. Meshing Pipeline

**Gmsh 워크플로우**:
```python
def generate_mesh(shape: Shape, params: MeshParams) -> Mesh:
    import gmsh

    gmsh.initialize()
    gmsh.model.add("koocad")

    # 1. Import STEP
    gmsh.merge(shape.export_temp_step())

    # 2. Set mesh size
    gmsh.option.setNumber("Mesh.CharacteristicLengthMin", params.min_size)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", params.max_size)

    # 3. Mesh algorithm
    gmsh.option.setNumber("Mesh.Algorithm3D", 10)  # HXT

    # 4. Generate
    gmsh.model.mesh.generate(3)

    # 5. Export to LS-DYNA format
    export_lsdyna(gmsh.model.mesh, "output.k")

    gmsh.finalize()
```

**LS-DYNA Keyword 생성**:
```python
def export_lsdyna(mesh, path):
    with open(path, 'w') as f:
        f.write("*KEYWORD\n")

        # Nodes
        f.write("*NODE\n")
        for node in mesh.getNodes():
            f.write(f"{node.id} {node.x} {node.y} {node.z}\n")

        # Elements (TET10)
        f.write("*ELEMENT_SOLID\n")
        for elem in mesh.getElements():
            f.write(f"{elem.id} {elem.part_id} " +
                    " ".join(map(str, elem.node_ids)) + "\n")

        # Part
        f.write("*PART\n")
        f.write("BGA Component\n")
        f.write(f"1 1\n")  # pid, secid

        # Material (PCB FR4)
        f.write("*MAT_ELASTIC\n")
        f.write("1 1.9e-9 19000 0.28\n")  # mid, rho, E, nu

        f.write("*END\n")
```

---

### 7. Batch Processing (Slurm)

**Job Array 예제**:
```bash
#!/bin/bash
#SBATCH --job-name=koocad_batch
#SBATCH --array=0-999  # 1000 cases
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --output=logs/%A_%a.out

# Load container
module load apptainer

# Get parameter set
PARAM_FILE="params/param_${SLURM_ARRAY_TASK_ID}.json"

# Run CAD generation
apptainer exec koocad.sif \
    python -m koocad.batch.generate \
    --params $PARAM_FILE \
    --output results/${SLURM_ARRAY_TASK_ID}
```

**Parameter sweep JSON**:
```json
{
  "sweep_type": "cartesian",
  "parameters": {
    "bga_size": [10, 12, 14, 16],
    "ball_pitch": [0.5, 0.65, 0.8, 1.0],
    "substrate_thickness": [0.6, 0.8, 1.0]
  },
  "output_formats": ["step", "stl", "dyna"],
  "mesh_quality": "high"
}
```

생성되는 케이스 수: 4 × 4 × 3 = **48 cases**

---

## 데이터 모델 (PostgreSQL)

```sql
-- Projects
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Parameter Sets
CREATE TABLE parameter_sets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    version INTEGER NOT NULL,
    params JSONB NOT NULL,
    checksum VARCHAR(64) UNIQUE,  -- SHA256 of params
    created_at TIMESTAMP DEFAULT NOW()
);

-- Jobs
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    parameter_set_id UUID REFERENCES parameter_sets(id),
    status VARCHAR(50),  -- pending, running, completed, failed
    kernel VARCHAR(50),  -- cadquery, occt
    result_path VARCHAR(500),  -- MinIO object key
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT
);

-- Exports
CREATE TABLE exports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id),
    format VARCHAR(20),  -- step, stl, glb, dyna
    file_path VARCHAR(500),
    file_size BIGINT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_parameter_sets_checksum ON parameter_sets(checksum);
CREATE INDEX idx_exports_job_id ON exports(job_id);
```

---

## 성능 목표

| 작업 | 목표 시간 | 현실적 시간 |
|------|-----------|-------------|
| Simple box 생성 | < 10ms | 5ms |
| BGA 15×15 생성 | < 200ms | 150ms |
| BGA 40×40 생성 | < 1s | 800ms |
| STEP export | < 100ms | 50ms |
| STL export (fine) | < 500ms | 300ms |
| Gmsh mesh (10K elem) | < 2s | 1.5s |
| LS-DYNA export | < 500ms | 200ms |

---

## 확장성 고려사항

### Horizontal Scaling
- FastAPI: Gunicorn workers (4-8 per node)
- Celery: Worker pool (autoscale 4-16)
- PostgreSQL: Read replicas (pgpool-II)
- MinIO: Distributed mode (4+ nodes)

### Caching Strategy
- L1: In-memory (LRU, 1GB)
- L2: Redis (10GB, 1 hour TTL)
- L3: MinIO (persistent)

### Rate Limiting
- Per-user: 100 req/min
- Per-IP: 500 req/min
- Batch API: 10 req/min

---

## 보안 설계

### Authentication
- JWT token (RS256)
- Refresh token (7 days)
- API key (batch jobs)

### Authorization
- RBAC (admin, user, guest)
- Resource-level ACL
- Audit log (all mutations)

### Data Protection
- Encryption at rest (MinIO SSE-S3)
- Encryption in transit (TLS 1.3)
- PII masking (logs)

---

## 모니터링 & 관측성

### Metrics (Prometheus)
- `koocad_jobs_total{status="completed"}` (counter)
- `koocad_job_duration_seconds` (histogram)
- `koocad_export_size_bytes` (histogram)

### Traces (OpenTelemetry)
- Request → Job → CAD Gen → Export
- 각 span에 parameter snapshot 첨부

### Logs (Loki)
- Structured JSON logs
- Correlation ID (trace_id)
- Error stack traces

---

## 재해 복구

### Backup
- PostgreSQL: WAL archiving (30 days)
- MinIO: Versioning enabled
- Config: Git repository

### Recovery
- RPO (Recovery Point Objective): 1 hour
- RTO (Recovery Time Objective): 4 hours
- Automated restore scripts

---

**작성일**: 2025-11-10
**버전**: 1.0.0
