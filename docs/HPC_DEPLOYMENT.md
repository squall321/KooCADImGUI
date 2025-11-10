# KooCAD HPC Deployment Guide

이 가이드는 HPC 클러스터에서 KooCAD를 배포하고 대량 배치 작업을 실행하는 방법을 설명합니다.

## 사전 요구사항

### HPC 클러스터 요구사항
- **Slurm**: 작업 스케줄러
- **Apptainer**: 컨테이너 런타임 (1.1.0+)
- **공유 스토리지**: NFS, Lustre, GPFS 등
- **데이터베이스**: PostgreSQL (네트워크 접근 가능)
- **객체 스토리지**: MinIO 또는 S3

### 선택적 요구사항
- **MPI**: 병렬 메싱 작업용
- **GPU**: 고급 렌더링/시각화용
- **InfiniBand**: 고성능 네트워킹

---

## 1. 컨테이너 빌드 및 배포

### 로컬에서 빌드

```bash
# 개발 머신에서
git clone https://github.com/yourusername/KooCADImGUI.git
cd KooCADImGUI

# 프로덕션 컨테이너 빌드
apptainer build koocad.sif koocad.def

# 컨테이너 검증
apptainer test koocad.sif
```

### HPC로 전송

```bash
# SCP로 전송
scp koocad.sif user@hpc-cluster:/shared/containers/

# 또는 공유 스토리지에 직접 빌드
ssh user@hpc-cluster
cd /shared/containers
apptainer build koocad.sif /path/to/koocad.def
```

---

## 2. 환경 설정

### 환경 변수 설정

`~/.koocad_env` 파일 생성:
```bash
export DATABASE_URL="postgresql://koocad:password@db-server.hpc.edu:5432/koocad"
export REDIS_URL="redis://cache-server.hpc.edu:6379/0"
export MINIO_ENDPOINT="storage-server.hpc.edu:9000"
export MINIO_ACCESS_KEY="your_access_key"
export MINIO_SECRET_KEY="your_secret_key"
export KOOCAD_CONTAINER="/shared/containers/koocad.sif"
```

Job 스크립트에서 사용:
```bash
source ~/.koocad_env
```

### 디렉토리 구조

```
/shared/koocad/
├── containers/
│   └── koocad.sif
├── params/
│   ├── params_0.json
│   ├── params_1.json
│   └── ...
├── results/
│   ├── job_12345/
│   │   ├── 0/
│   │   │   ├── model.step
│   │   │   ├── model.stl
│   │   │   └── model.k
│   │   └── 1/
│   └── job_12346/
└── logs/
    ├── koocad_12345_0.out
    └── koocad_12345_0.err
```

---

## 3. 파라미터 생성

### 단일 파라미터 세트

```json
// /shared/koocad/params/params_0.json
{
  "component_type": "bga",
  "substrate_width": 12.0,
  "substrate_height": 12.0,
  "substrate_thickness": 0.8,
  "ball_pitch": 0.8,
  "ball_diameter": 0.4,
  "ball_rows": 15,
  "ball_cols": 15,
  "ball_pattern": "full"
}
```

### 파라미터 스윕 생성

```yaml
# sweep_config.yaml
sweep_type: cartesian
parameters:
  substrate_width: [10.0, 12.0, 14.0]
  ball_pitch: [0.5, 0.65, 0.8]
  substrate_thickness: [0.6, 0.8, 1.0]

fixed_parameters:
  component_type: "bga"
  ball_pattern: "full"

output:
  formats: ["step", "stl", "dyna"]
  mesh_quality: "high"
```

생성:
```bash
apptainer exec $KOOCAD_CONTAINER \
    koocad sweep generate \
    --config sweep_config.yaml \
    --output /shared/koocad/params/
```

---

## 4. Slurm Job 제출

### 기본 Job Array

```bash
#!/bin/bash
#SBATCH --job-name=koocad_bga
#SBATCH --output=/shared/koocad/logs/koocad_%A_%a.out
#SBATCH --error=/shared/koocad/logs/koocad_%A_%a.err
#SBATCH --array=0-26        # 27개 케이스 (3x3x3)
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=00:30:00

source ~/.koocad_env

PARAM_FILE="/shared/koocad/params/params_${SLURM_ARRAY_TASK_ID}.json"
OUTPUT_DIR="/shared/koocad/results/${SLURM_ARRAY_JOB_ID}/${SLURM_ARRAY_TASK_ID}"

mkdir -p "$OUTPUT_DIR"

apptainer exec \
    --bind /shared/koocad:/work \
    $KOOCAD_CONTAINER \
    koocad generate \
        --params "$PARAM_FILE" \
        --output "$OUTPUT_DIR" \
        --format step stl dyna
```

제출:
```bash
sbatch job_array.sh
```

### 고급: MPI 병렬화

```bash
#!/bin/bash
#SBATCH --job-name=koocad_mpi
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=8
#SBATCH --cpus-per-task=4
#SBATCH --time=02:00:00

module load openmpi/4.1

mpirun -n 16 apptainer exec \
    --bind /shared/koocad:/work \
    $KOOCAD_CONTAINER \
    koocad generate-parallel \
        --params-dir /work/params \
        --output-dir /work/results
```

### GPU 사용 (렌더링/시각화)

```bash
#!/bin/bash
#SBATCH --gres=gpu:1
#SBATCH --partition=gpu

apptainer exec \
    --nv \
    --bind /shared/koocad:/work \
    $KOOCAD_CONTAINER \
    koocad render \
        --input model.step \
        --output render.png \
        --resolution 4096x4096
```

---

## 5. 작업 모니터링

### Slurm 명령어

```bash
# 작업 상태 확인
squeue -u $USER

# 특정 job array 상태
squeue -j 12345

# 완료된 작업 정보
sacct -j 12345 --format=JobID,State,ExitCode,Elapsed

# 로그 확인
tail -f /shared/koocad/logs/koocad_12345_0.out
```

### KooCAD 모니터링 대시보드 (선택)

```bash
# Prometheus 메트릭 수집
apptainer exec $KOOCAD_CONTAINER \
    koocad monitor \
    --job-id 12345 \
    --export-prometheus metrics.txt
```

---

## 6. 결과 수집 및 후처리

### 결과 아카이브

```bash
# 완료된 작업 결과 압축
cd /shared/koocad/results
tar -czf job_12345_results.tar.gz job_12345/

# S3로 업로드 (장기 보관)
aws s3 cp job_12345_results.tar.gz s3://koocad-archive/
```

### 통계 생성

```bash
apptainer exec $KOOCAD_CONTAINER \
    koocad stats \
    --input /shared/koocad/results/job_12345 \
    --output summary.json
```

---

## 7. 최적화 팁

### 파일시스템 최적화

**Lustre 스트라이핑:**
```bash
# 큰 파일용 스트라이핑 설정
lfs setstripe -c 4 /shared/koocad/results
```

**버스트 버퍼 사용:**
```bash
#SBATCH --bb=20GB

# Fast tier에 임시 데이터 저장
$DW_JOB_STRIPED/temp_results
```

### 메모리 최적화

```python
# koocad_config.yaml
cache:
  max_memory: "6GB"
  cleanup_threshold: 0.8

geometry:
  tessellation_quality: "medium"
  batch_size: 50
```

### CPU/GPU 할당

```bash
# CPU-bound tasks
#SBATCH --cpus-per-task=8
#SBATCH --mem-per-cpu=2G

# GPU-accelerated
#SBATCH --gres=gpu:a100:1
#SBATCH --mem=64G
```

---

## 8. 문제 해결

### 컨테이너 권한 문제

```bash
# Fakeroot 빌드
apptainer build --fakeroot koocad.sif koocad.def

# Sandbox 모드 (디버깅용)
apptainer build --sandbox koocad/ koocad.def
apptainer shell --writable koocad/
```

### 네트워크 연결 실패

```bash
# DNS 확인
apptainer exec koocad.sif nslookup db-server.hpc.edu

# 연결 테스트
apptainer exec koocad.sif \
    psql $DATABASE_URL -c "SELECT version();"
```

### 메모리 부족

```bash
# 메모리 프로파일링
apptainer exec koocad.sif \
    python -m memory_profiler generate.py

# Swap 증가 (일시적)
#SBATCH --mem=16G
#SBATCH --tmp=32G
```

---

## 9. 예제: 1000 케이스 BGA 생성

```bash
# 1. 파라미터 생성 (1000개)
cat > sweep_large.yaml <<EOF
sweep_type: sobol
n_samples: 1000
parameters:
  substrate_width: [8.0, 20.0]
  ball_pitch: [0.4, 1.0]
  substrate_thickness: [0.5, 1.5]
EOF

koocad sweep generate --config sweep_large.yaml --output /shared/koocad/params/

# 2. Job 제출
sbatch --array=0-999 scripts/slurm-batch-job.sh

# 3. 결과 대기 (병렬 실행 시 ~2시간)

# 4. 통계 생성
koocad stats --input /shared/koocad/results/job_*/  --output stats.csv
```

---

## 10. 참고 자료

- [Apptainer User Guide](https://apptainer.org/docs/user/main/)
- [Slurm Job Array](https://slurm.schedmd.com/job_array.html)
- [KooCAD API Documentation](../api/)
- [Troubleshooting Guide](./TROUBLESHOOTING.md)

---

**문의**: hpc-support@koocad.com
