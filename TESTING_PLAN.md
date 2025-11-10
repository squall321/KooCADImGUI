# KooCAD Testing Plan

## 테스트 현황

**현재 상태**: 145 phases 구현 완료, 테스트 미실시 ⚠️

**목표**: 모든 핵심 기능의 동작 검증

## 테스트 레벨

### Level 0: 기본 환경 테스트 (즉시 실행 가능)
### Level 1: Unit Tests (모듈별 독립 테스트)
### Level 2: Integration Tests (모듈 간 연동)
### Level 3: System Tests (전체 시스템)
### Level 4: End-to-End Tests (실제 시나리오)

---

## Level 0: 기본 환경 테스트 (의존성 없음)

### ✅ Phase 1-35: Core Infrastructure

#### Test 0.1: Import Tests
```bash
# 목표: 모든 모듈이 import 가능한지 확인
python -c "import koocad.core.parameters"
python -c "import koocad.core.expression"
python -c "import koocad.core.validation"
python -c "import koocad.core.serialization"
python -c "import koocad.core.shape"
```

**예상 결과**: ImportError 없이 성공
**실패 시**: Missing dependencies or syntax errors

#### Test 0.2: Parameter Creation
```python
from koocad.core.parameters import FloatParameter, IntParameter

# 파라미터 생성 테스트
fp = FloatParameter("width", 10.0, min_val=0.0, max_val=100.0)
ip = IntParameter("count", 5, min_val=1, max_val=10)

assert fp.name == "width"
assert fp.value == 10.0
assert ip.value == 5
print("✓ Parameter creation works")
```

#### Test 0.3: Expression Evaluation
```python
from koocad.core.expression import ExpressionEngine

engine = ExpressionEngine()
engine.set_variable("a", 10.0)
engine.set_variable("b", 20.0)

result = engine.evaluate("a + b * 2")
assert result == 50.0
print("✓ Expression evaluation works")
```

#### Test 0.4: Validation
```python
from koocad.core.validation import ValidationEngine

validator = ValidationEngine()
validator.add_constraint("width", lambda w: w > 0, "Width must be positive")

assert validator.validate({"width": 10.0})
assert not validator.validate({"width": -5.0})
print("✓ Validation works")
```

---

## Level 1: Unit Tests (CadQuery 필요)

### ⚠️ Phase 36-85: CAD Generators (requires CadQuery)

#### Test 1.1: BGA Generator
```python
# pip install cadquery 필요
from koocad.generators.bga import BGAGenerator

try:
    gen = BGAGenerator(
        substrate_width=12.0,
        substrate_height=12.0,
        ball_rows=5,
        ball_cols=5,
    )
    shape = gen.generate()

    volume = shape.volume()
    assert volume > 0, "Volume should be positive"

    bbox = shape.bounding_box()
    assert len(bbox) == 2, "Bounding box should have min and max"

    print(f"✓ BGA generation works (volume: {volume:.2f} mm³)")

except ImportError as e:
    print(f"⚠ CadQuery not installed: {e}")
    print("  Install with: pip install cadquery")
except Exception as e:
    print(f"✗ BGA generation failed: {e}")
```

#### Test 1.2: MLCC Generator
```python
from koocad.generators.passives import MLCCGenerator

try:
    gen = MLCCGenerator(
        body_length=2.0,
        body_width=1.25,
        body_height=1.25,
    )
    shape = gen.generate()
    assert shape.volume() > 0
    print("✓ MLCC generation works")
except ImportError:
    print("⚠ CadQuery not installed")
except Exception as e:
    print(f"✗ MLCC generation failed: {e}")
```

---

## Level 2: Integration Tests

### Phase 86-105: UI System

#### Test 2.1: UI Import Test
```bash
python -c "import koocad.ui.app"
python -c "import koocad.ui.node_editor"
python -c "import koocad.ui.graph_executor"
```

**예상 결과**: DearPyGui 없으면 ImportError (정상)

#### Test 2.2: Graph Execution
```python
from koocad.ui.graph_executor import GraphExecutor
from koocad.ui.node_editor import Node

executor = GraphExecutor()

# Mock nodes
class MockNode(Node):
    def __init__(self, node_id, value):
        super().__init__(node_id, "Mock")
        self.value = value

    def execute(self, inputs):
        return {"output": self.value}

nodes = {
    1: MockNode(1, 10),
    2: MockNode(2, 20),
}
links = []

results = executor.execute_graph(nodes, links)
assert len(results) == 2
print("✓ Graph execution works")
```

---

## Level 3: System Tests (FastAPI Backend)

### Phase 106-120: Backend API

#### Test 3.1: FastAPI Import
```bash
python -c "from koocad.backend.main import app; print('✓ FastAPI app loads')"
```

#### Test 3.2: Database Models
```python
from koocad.backend.models.user import User, UserRole
from koocad.backend.models.job import Job, JobStatus, JobType

# Check enums
assert UserRole.ADMIN == "admin"
assert JobStatus.PENDING == "pending"
assert JobType.CAD_GENERATION == "cad_generation"

print("✓ Database models defined correctly")
```

#### Test 3.3: API Endpoints (requires server)
```bash
# Start server in background
uvicorn koocad.backend.main:app --host 0.0.0.0 --port 8000 &
sleep 5

# Test endpoints
curl -s http://localhost:8000/ | grep "KooCAD Backend"
curl -s http://localhost:8000/health | grep "healthy"

# Stop server
pkill -f uvicorn
```

---

## Level 4: End-to-End Tests

### Complete Workflow Test

#### Test 4.1: CAD Generation → Export → Meshing
```python
#!/usr/bin/env python
"""
Complete workflow test:
1. Generate BGA
2. Export to STEP
3. Export to STL
4. Mesh with Gmsh
5. Check quality
"""

from pathlib import Path
import sys

output_dir = Path("test_output")
output_dir.mkdir(exist_ok=True)

print("=" * 70)
print("KooCAD Complete Workflow Test")
print("=" * 70)

# Step 1: Generate CAD
print("\n1. Generating BGA...")
try:
    from koocad.generators.bga import BGAGenerator

    gen = BGAGenerator(
        substrate_width=10.0,
        substrate_height=10.0,
        ball_rows=5,
        ball_cols=5,
    )
    shape = gen.generate()
    print(f"   ✓ Generated (volume: {shape.volume():.2f} mm³)")
except ImportError:
    print("   ✗ CadQuery not installed")
    sys.exit(1)
except Exception as e:
    print(f"   ✗ Failed: {e}")
    sys.exit(1)

# Step 2: Export to STEP
print("\n2. Exporting to STEP...")
try:
    from koocad.exporters.step import STEPExporter

    exporter = STEPExporter()
    step_file = exporter.export(shape, output_dir / "test.step")

    assert step_file.exists()
    print(f"   ✓ Exported: {step_file}")
except Exception as e:
    print(f"   ✗ Failed: {e}")

# Step 3: Export to STL
print("\n3. Exporting to STL...")
try:
    from koocad.exporters.stl import STLExporter

    exporter = STLExporter(binary=True)
    stl_file = exporter.export(shape, output_dir / "test.stl")

    assert stl_file.exists()
    print(f"   ✓ Exported: {stl_file}")
except Exception as e:
    print(f"   ✗ Failed: {e}")

# Step 4: Mesh with Gmsh
print("\n4. Meshing with Gmsh...")
try:
    from koocad.meshing.gmsh_mesher import GmshMesher

    mesher = GmshMesher(element_size=1.0)
    node_count, elem_count = mesher.mesh(shape, output_dir / "test.msh")

    print(f"   ✓ Mesh created: {node_count} nodes, {elem_count} elements")
except ImportError:
    print("   ⚠ Gmsh not installed")
except Exception as e:
    print(f"   ⚠ Failed: {e}")

# Step 5: Quality check
print("\n5. Checking mesh quality...")
try:
    from koocad.meshing.quality import MeshQualityChecker

    # Mock data for demo
    nodes = [(0, 0, 0), (1, 0, 0), (0.5, 1, 0), (0.5, 0.5, 1)]
    elements = [[0, 1, 2, 3]]

    checker = MeshQualityChecker()
    aspect = checker.check_aspect_ratio(nodes, elements)

    print(f"   ✓ Aspect ratio: {aspect['mean']:.3f}")
except Exception as e:
    print(f"   ⚠ Failed: {e}")

print("\n" + "=" * 70)
print("Workflow test complete!")
print(f"Output files in: {output_dir}")
print("=" * 70)
```

---

## Test Execution Plan

### Phase 1: 기본 검증 (5분)
```bash
# 1. Import 테스트
./tests/test_imports.sh

# 2. 기본 기능 테스트
pytest tests/test_validation.py -v
pytest tests/test_serialization.py -v

# 3. 파라미터 테스트
python tests/manual/test_parameters.py
```

### Phase 2: CAD 생성 테스트 (CadQuery 필요, 10분)
```bash
# CadQuery 설치
pip install cadquery

# BGA 테스트
python examples/01_basic_bga.py

# 모든 생성기 테스트
python tests/manual/test_all_generators.py
```

### Phase 3: UI 테스트 (DearPyGui 필요, 5분)
```bash
# DearPyGui 설치
pip install dearpygui

# UI 실행 테스트 (수동)
python examples/09_integrated_ui_demo.py
# - Add node 버튼 클릭
# - Parameter 조정
# - Execute graph 버튼 클릭
# - 에러 없이 실행되는지 확인
```

### Phase 4: Backend 테스트 (15분)
```bash
# Backend 의존성 설치
pip install fastapi uvicorn sqlalchemy asyncpg celery redis

# 1. Database 준비
docker run -d --name koocad-test-db \
  -e POSTGRES_DB=koocad_test \
  -e POSTGRES_USER=test \
  -e POSTGRES_PASSWORD=test \
  -p 5432:5432 postgres:15

# 2. Redis 준비
docker run -d --name koocad-test-redis -p 6379:6379 redis:7

# 3. API 서버 시작
export DATABASE_URL="postgresql://test:test@localhost:5432/koocad_test"
uvicorn koocad.backend.main:app --port 8000 &

# 4. API 테스트
curl http://localhost:8000/health
curl http://localhost:8000/ready

# 5. 종료
pkill uvicorn
docker stop koocad-test-db koocad-test-redis
docker rm koocad-test-db koocad-test-redis
```

### Phase 5: Export 테스트 (5분)
```bash
python examples/11_export_meshing_demo.py

# 출력 파일 확인
ls -lh output/exports/
ls -lh output/mesh/
ls -lh output/lsdyna/

# 파일 크기 확인 (0보다 커야 함)
test -s output/exports/bga.step && echo "✓ STEP file created"
test -s output/exports/bga.stl && echo "✓ STL file created"
```

### Phase 6: HPC 테스트 (5분)
```bash
python examples/12_hpc_batch_demo.py

# 출력 파일 확인
ls -lh output/hpc/

# Slurm 스크립트 검증
bash -n output/hpc/job_single.sh && echo "✓ Script syntax valid"
bash -n output/hpc/job_array.sh && echo "✓ Array script syntax valid"

# Container 정의 검증
grep "Bootstrap: docker" output/hpc/koocad.def && echo "✓ Container def valid"
```

---

## 자동화된 테스트 스크립트

### Master Test Script

```bash
#!/bin/bash
# tests/run_all_tests.sh

set -e

echo "================================"
echo "KooCAD Complete Test Suite"
echo "================================"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

failed=0
passed=0

run_test() {
    local test_name="$1"
    local test_command="$2"

    echo ""
    echo "Testing: $test_name"
    echo "----------------------------------------"

    if eval "$test_command"; then
        echo -e "${GREEN}✓ PASSED${NC}: $test_name"
        ((passed++))
    else
        echo -e "${RED}✗ FAILED${NC}: $test_name"
        ((failed++))
    fi
}

# Level 0: Basic imports
run_test "Core imports" "python -c 'import koocad.core.parameters'"
run_test "Generator imports" "python -c 'import koocad.generators.bga'"
run_test "UI imports" "python -c 'import koocad.ui.node_editor'"
run_test "Backend imports" "python -c 'import koocad.backend.main'"
run_test "Exporter imports" "python -c 'import koocad.exporters.step'"
run_test "HPC imports" "python -c 'import koocad.hpc.slurm'"

# Level 1: Unit tests
run_test "Validation tests" "pytest tests/test_validation.py -v"
run_test "Serialization tests" "pytest tests/test_serialization.py -v"

# Level 2: Integration tests (if CadQuery available)
if python -c "import cadquery" 2>/dev/null; then
    run_test "BGA generation" "python examples/01_basic_bga.py"
else
    echo -e "${YELLOW}⚠ SKIPPED${NC}: BGA generation (CadQuery not installed)"
fi

# Level 3: Export tests
run_test "Export demo" "python examples/11_export_meshing_demo.py"

# Level 4: HPC tests
run_test "HPC demo" "python examples/12_hpc_batch_demo.py"

# Summary
echo ""
echo "================================"
echo "Test Summary"
echo "================================"
echo -e "Passed: ${GREEN}$passed${NC}"
echo -e "Failed: ${RED}$failed${NC}"
echo "Total: $((passed + failed))"

if [ $failed -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
fi
```

---

## 예상 문제점 및 해결책

### 문제 1: Import Errors
**증상**: `ImportError: No module named 'koocad'`
**원인**: 패키지 미설치
**해결**: `pip install -e .`

### 문제 2: CadQuery 의존성
**증상**: CadQuery import 실패
**원인**: CadQuery 미설치 (설치가 복잡함)
**해결**:
- `pip install cadquery` (실패 가능)
- Conda: `conda install -c conda-forge cadquery`
- Docker: `docker pull cadquery/cadquery`

### 문제 3: DearPyGui 충돌
**증상**: UI 실행 시 segfault
**원인**: OpenGL 드라이버 문제
**해결**:
- `export LIBGL_ALWAYS_SOFTWARE=1`
- 헤드리스 환경에서는 UI 스킵

### 문제 4: Database 연결
**증상**: PostgreSQL connection refused
**원인**: PostgreSQL 미실행
**해결**: Docker로 빠른 시작

### 문제 5: Slurm 명령어
**증상**: `sbatch: command not found`
**원인**: Slurm 미설치 (HPC 환경 필요)
**해결**: 스크립트 생성만 테스트 (제출은 스킵)

---

## 최소 테스트 (5분, 의존성 최소)

```bash
# 1. Import 테스트
python -c "import koocad.core.parameters; print('✓ Core OK')"
python -c "import koocad.generators.bga; print('✓ Generators OK')"
python -c "import koocad.backend.main; print('✓ Backend OK')"
python -c "import koocad.exporters.step; print('✓ Exporters OK')"
python -c "import koocad.hpc.slurm; print('✓ HPC OK')"

# 2. 기본 기능 테스트
python -c "
from koocad.core.parameters import FloatParameter
p = FloatParameter('test', 10.0)
assert p.value == 10.0
print('✓ Parameters work')
"

# 3. 예제 스크립트 실행
python examples/12_hpc_batch_demo.py

echo ""
echo "✓ Minimum tests passed!"
echo "For full tests, install: pip install cadquery gmsh fastapi"
```

---

## 테스트 체크리스트

- [ ] Import tests (Level 0)
- [ ] Parameter creation (Level 0)
- [ ] Expression evaluation (Level 0)
- [ ] Validation (Level 0)
- [ ] BGA generation (Level 1, needs CadQuery)
- [ ] MLCC generation (Level 1, needs CadQuery)
- [ ] Graph execution (Level 2)
- [ ] Backend models (Level 3)
- [ ] API endpoints (Level 3, needs server)
- [ ] STEP export (Level 4, needs CadQuery)
- [ ] STL export (Level 4, needs CadQuery)
- [ ] Gmsh meshing (Level 4, needs Gmsh)
- [ ] HPC scripts (Level 4)
- [ ] Parameter sweep (Level 4)

---

## 다음 단계

1. **즉시 실행 가능한 테스트 먼저 수행**
   ```bash
   python -c "import koocad.core.parameters"
   python tests/test_validation.py
   python examples/12_hpc_batch_demo.py
   ```

2. **의존성 설치 후 추가 테스트**
   ```bash
   pip install cadquery
   python examples/01_basic_bga.py
   ```

3. **문제 발견 시 수정**
   - Import errors → `__init__.py` 수정
   - Logic errors → 해당 모듈 수정
   - Missing dependencies → requirements 업데이트

4. **CI/CD 설정**
   - GitHub Actions
   - 자동화된 테스트 실행
   - Coverage 리포트

제가 테스트 스크립트를 만들어서 실제로 실행해볼까요?
