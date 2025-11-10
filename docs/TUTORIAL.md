## KooCAD Tutorial - Getting Started

이 튜토리얼은 KooCAD를 사용하여 파라메트릭 전자부품 CAD 모델을 생성하는 방법을 단계별로 안내합니다.

---

## 목차

1. [설치](#1-설치)
2. [첫 번째 프로젝트 생성](#2-첫-번째-프로젝트-생성)
3. [파라미터 정의하기](#3-파라미터-정의하기)
4. [BGA 패키지 생성](#4-bga-패키지-생성)
5. [파라미터 스윕](#5-파라미터-스윕)
6. [HPC 배치 실행](#6-hpc-배치-실행)

---

## 1. 설치

### Python 환경

```bash
# Python 3.11+ 필요
python --version

# 가상 환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# KooCAD 설치
pip install -e ".[all]"
```

### Apptainer (HPC 환경)

```bash
# Apptainer 컨테이너 빌드
bash scripts/build-containers.sh

# 컨테이너로 진입
apptainer shell --bind $(pwd)/src:/opt/koocad/src koocad-dev.sif
```

### 인프라 서비스

**옵션 A: 시스템 서비스 (권장)**
```bash
sudo systemctl start postgresql redis-server minio
```

**옵션 B: Docker로 로컬 서비스만 실행**
```bash
docker run -d --name koocad-postgres -p 5432:5432 \
    -e POSTGRES_USER=koocad -e POSTGRES_DB=koocad postgres:16-alpine
docker run -d --name koocad-redis -p 6379:6379 redis:7-alpine
docker run -d --name koocad-minio -p 9000:9000 \
    minio/minio server /data
```

---

## 2. 첫 번째 프로젝트 생성

```bash
# 프로젝트 초기화
koocad init my_bga_project

# 프로젝트 구조 확인
cd my_bga_project
tree
# my_bga_project/
# ├── params/         # 파라미터 파일
# ├── results/        # 생성된 CAD 파일
# ├── scripts/        # 커스텀 스크립트
# ├── config/         # 설정 파일
# └── README.md
```

---

## 3. 파라미터 정의하기

### 기본 파라미터 (Python API)

```python
from koocad.core.parameters import FloatParameter, IntParameter, ParameterSet, Unit

# ParameterSet 생성
params = ParameterSet()

# 기판 크기
params.add(FloatParameter(
    name="substrate_width",
    description="BGA 기판 너비",
    value=12.0,
    min_value=5.0,
    max_value=50.0,
    unit=Unit.MM,
))

params.add(FloatParameter(
    name="substrate_height",
    value=12.0,
    unit=Unit.MM,
))

params.add(FloatParameter(
    name="substrate_thickness",
    value=0.8,
    unit=Unit.MM,
))

# 볼 배열
params.add(IntParameter(
    name="ball_rows",
    value=15,
    min_value=2,
    max_value=50,
))

params.add(FloatParameter(
    name="ball_pitch",
    value=0.8,
    unit=Unit.MM,
))

# 모든 파라미터 평가
values = params.evaluate_all()
print(f"총 {len(values)}개 파라미터 평가 완료")
```

### Expression 파라미터

```python
from koocad.core.parameters import ExpressionParameter

# 계산된 파라미터 추가
params.add(ExpressionParameter(
    name="array_width",
    description="볼 배열 전체 너비",
    value="(ball_cols - 1) * ball_pitch",
    dependencies=["ball_cols", "ball_pitch"],
))

params.add(ExpressionParameter(
    name="total_balls",
    value="ball_rows * ball_cols",
    dependencies=["ball_rows", "ball_cols"],
))

# 평가
result = params.evaluate_all()
print(f"배열 너비: {result['array_width']:.2f} mm")
print(f"총 볼 개수: {result['total_balls']:.0f}")
```

---

## 4. BGA 패키지 생성

### 프리셋 사용

```python
from koocad.core.presets import PresetLibrary

# 프리셋 라이브러리 로드
library = PresetLibrary()

# JEDEC 표준 BGA 프리셋
bga_params = library.get("BGA_15x15_0.8mm")

# 파라미터 확인
values = bga_params.evaluate_all()
for name, value in values.items():
    print(f"{name}: {value}")
```

### 커스텀 파라미터

```python
# 프리셋에서 시작해서 수정
custom_params = library.get("BGA_15x15_0.8mm")

# 값 변경
custom_params.set_value("substrate_width", 14.0)
custom_params.set_value("ball_pitch", 0.65)

# TODO: CAD 생성 (Phase 31-50에서 구현 예정)
# generator = BGAGenerator()
# shape = generator.generate(custom_params)
# shape.export_step("my_bga.step")
```

---

## 5. 파라미터 스윕

### Cartesian Product Sweep

```yaml
# sweep_config.yaml
sweep_type: cartesian
parameters:
  substrate_width: [10.0, 12.0, 14.0]
  ball_pitch: [0.5, 0.65, 0.8]
  substrate_thickness: [0.6, 0.8, 1.0]

output_formats: [step, stl]
```

```bash
# 파라미터 파일 생성 (3×3×3 = 27 cases)
koocad sweep generate -c sweep_config.yaml -o params/
```

### Random Sampling (Monte Carlo)

```yaml
# random_sweep.yaml
sweep_type: random
n_samples: 100
parameters:
  substrate_width: [8.0, 20.0]  # min, max
  ball_pitch: [0.4, 1.0]
  substrate_thickness: [0.5, 1.5]
```

```bash
# 랜덤 샘플 100개 생성
koocad sweep generate -c random_sweep.yaml -o params/
```

---

## 6. HPC 배치 실행

### Slurm Job Array

```bash
# 파라미터 생성 (1000개)
koocad sweep generate -c large_sweep.yaml -o /scratch/params/

# Slurm job 제출
sbatch --array=0-999 scripts/slurm-batch-job.sh
```

### Job 모니터링

```bash
# 작업 상태 확인
squeue -u $USER

# 로그 확인
tail -f logs/koocad_<job_id>_<array_id>.out

# 완료된 작업 통계
sacct -j <job_id> --format=JobID,State,ExitCode,Elapsed
```

---

## 7. 고급 기능

### History & Undo/Redo

```python
from koocad.core.history import History, SetParameterValueCommand

history = History()

# 파라미터 변경 (자동으로 history에 기록)
cmd = SetParameterValueCommand(params, "substrate_width", 15.0)
history.execute(cmd)

# Undo
description = history.undo()
print(f"Undo: {description}")

# Redo
description = history.redo()
print(f"Redo: {description}")
```

### Snapshot 관리

```python
from koocad.core.history import SnapshotManager

manager = SnapshotManager()

# 스냅샷 생성
snapshot1 = manager.take_snapshot(params, "Initial design")
snapshot2 = manager.take_snapshot(params, "After optimization")

# 스냅샷 복원
manager.restore_snapshot(params, snapshot_index=0)

# 변경사항 diff
diff = manager.diff_snapshots(0, 1)
for param, (old, new) in diff.items():
    print(f"{param}: {old} → {new}")
```

### Constraint Solver

```python
from koocad.core.constraints import CSPSolver, BinaryConstraint

solver = CSPSolver()

# 변수 및 도메인 정의
solver.add_variable("substrate_width", [10, 12, 14, 16])
solver.add_variable("array_width", [8, 10, 12, 14])

# 제약조건 추가 (array_width < substrate_width)
solver.add_constraint(
    BinaryConstraint(
        "array_width",
        "substrate_width",
        lambda array, substrate: array < substrate - 1.0
    )
)

# 해 찾기
solution = solver.solve()
print(f"Valid solution: {solution}")
```

---

## 다음 단계

- [API Reference](../api/) - 전체 API 문서
- [Component Library](../components/) - 전자부품 라이브러리
- [HPC Deployment](HPC_DEPLOYMENT.md) - HPC 배포 가이드
- [Examples](../../examples/) - 예제 코드

---

**질문이나 도움이 필요하신가요?**
- GitHub Issues: https://github.com/yourusername/KooCADImGUI/issues
- 이메일: dev@koocad.com
