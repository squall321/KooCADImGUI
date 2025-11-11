# KooCAD 빠른 시작 가이드

5분 안에 KooCAD를 시작하는 방법입니다.

## 📦 설치

### 1단계: Python 환경 준비

```bash
# Python 3.11 이상 필요
python --version  # Python 3.11.x 이상 확인

# 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2단계: KooCAD 설치

```bash
# 저장소 클론
git clone https://github.com/your-org/KooCADImGUI.git
cd KooCADImGUI

# 최소 설치 (파라미터 시스템만)
pip install pydantic sympy numpy pytest
```

### 3단계: 설치 확인

```bash
# 테스트 실행
python -m pytest tests/ -v

# 예제 실행
python examples/00_basic_parameters_corrected.py
```

## 🚀 첫 번째 프로그램

### BGA 파라미터 생성

```python
# my_first_bga.py
import sys
sys.path.insert(0, 'src')

from koocad.core.presets import BGAPresets

# JEDEC 표준 BGA 프리셋 로드
bga = BGAPresets.get('BGA_15x15_0.8mm')

# 파라미터 확인
values = bga.evaluate_all()
print(f"볼 수: {values['ball_rows']} x {values['ball_cols']}")
print(f"피치: {values['ball_pitch']} mm")
print(f"기판 크기: {values['substrate_width']} x {values['substrate_height']} mm")
```

실행:
```bash
python my_first_bga.py
```

출력:
```
볼 수: 15 x 15
피치: 0.8 mm
기판 크기: 13.2 x 13.2 mm
```

### 커스텀 파라미터 만들기

```python
from koocad.core.parameters import FloatParameter, ParameterSet, ExpressionParameter

# 파라미터 세트 생성
params = ParameterSet()

# 기본 치수
params.add(FloatParameter(
    name='width',
    value=10.0,
    min_value=5.0,
    max_value=20.0,
    unit='mm'
))

params.add(FloatParameter(
    name='height',
    value=8.0,
    min_value=5.0,
    max_value=20.0,
    unit='mm'
))

# 표현식으로 면적 계산
params.add(ExpressionParameter(
    name='area',
    value='width * height'
))

# 모든 파라미터 평가
result = params.evaluate_all()
print(f"면적: {result['area']} mm²")  # 80.0 mm²
```

## 📚 다음 단계

### 더 많은 예제

```bash
# 프리셋 라이브러리 탐색
python examples/01_basic_parameters.py

# 표현식 엔진 사용
python examples/02_expression_engine.py

# 검증 시스템
python examples/04_validation_and_serialization.py
```

### CAD 생성 (선택사항)

CAD 모델 생성을 위해서는 CadQuery 설치가 필요합니다:

```bash
# Conda 사용 (권장)
conda install -c conda-forge cadquery

# 또는 pip
pip install cadquery
```

### 백엔드 API 실행 (선택사항)

```bash
# 의존성 설치
pip install fastapi uvicorn sqlalchemy redis celery

# PostgreSQL, Redis 실행 (Docker)
docker-compose up -d

# API 서버 시작
koocad-server
```

웹 브라우저에서 http://localhost:8000/docs 접속

## 🆘 문제 해결

### ImportError 발생 시

```bash
# PYTHONPATH 설정
export PYTHONPATH=/path/to/KooCADImGUI/src:$PYTHONPATH

# 또는 sys.path 수정
import sys
sys.path.insert(0, 'src')
```

### 테스트 실패 시

```bash
# pytest가 없는 경우
pip install pytest pytest-cov

# 특정 테스트만 실행
python -m pytest tests/test_parameters.py -v
```

### CadQuery 설치 실패 시

```bash
# Conda 환경 사용 (가장 안정적)
conda create -n koocad python=3.11
conda activate koocad
conda install -c conda-forge cadquery
```

## 📖 추가 자료

- [상세 설치 가이드](INSTALLATION.md)
- [아키텍처 문서](ARCHITECTURE.md)
- [API 문서](docs/API.md)
- [테스트 결과](TEST_RESULTS.md)
- [개발 계획](MASTER_PLAN.md)

## 💬 도움 받기

- GitHub Issues: https://github.com/your-org/KooCADImGUI/issues
- 문서: https://koocad.readthedocs.io
- 예제 코드: `examples/` 디렉토리

---

**환영합니다!** KooCAD는 완전 파라메트릭 전자부품 CAD 자동화 시스템입니다.
