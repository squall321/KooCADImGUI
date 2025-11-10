# Contributing to KooCAD

Thank you for your interest in contributing to KooCAD! 🎉

## 목차

- [행동 강령](#행동-강령)
- [개발 환경 설정](#개발-환경-설정)
- [개발 워크플로우](#개발-워크플로우)
- [코드 스타일](#코드-스타일)
- [커밋 메시지 규칙](#커밋-메시지-규칙)
- [Pull Request 프로세스](#pull-request-프로세스)
- [테스팅](#테스팅)
- [문서화](#문서화)

---

## 행동 강령

이 프로젝트는 [Contributor Covenant](CODE_OF_CONDUCT.md) 행동 강령을 따릅니다. 참여함으로써 귀하는 이 규칙을 준수하는 데 동의합니다.

---

## 개발 환경 설정

### 1. Repository Fork & Clone

```bash
# Fork the repository on GitHub
git clone https://github.com/YOUR_USERNAME/KooCADImGUI.git
cd KooCADImGUI
git remote add upstream https://github.com/ORIGINAL_OWNER/KooCADImGUI.git
```

### 2. Python 환경 설정

```bash
# Python 3.11+ 필수
python --version  # 3.11 이상인지 확인

# Virtual environment 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 개발 의존성 설치
pip install -e ".[dev]"
```

### 3. Pre-commit Hooks 설치

```bash
pre-commit install
```

### 4. Docker 환경 시작

```bash
docker-compose up -d
```

### 5. 데이터베이스 마이그레이션

```bash
alembic upgrade head
```

---

## 개발 워크플로우

### Branch 전략

- `main`: 프로덕션 릴리스
- `develop`: 개발 브랜치 (기본)
- `feature/*`: 새 기능 (예: `feature/bga-generator`)
- `bugfix/*`: 버그 수정 (예: `bugfix/parameter-validation`)
- `hotfix/*`: 긴급 수정 (예: `hotfix/security-patch`)

### 새 기능 개발

```bash
# develop에서 시작
git checkout develop
git pull upstream develop

# feature 브랜치 생성
git checkout -b feature/your-feature-name

# 개발 진행
# ...

# 커밋
git add .
git commit -m "feat: add BGA ball map generator"

# Push
git push origin feature/your-feature-name

# GitHub에서 Pull Request 생성
```

---

## 코드 스타일

### Python (PEP 8 + Black)

```python
# Good
class BGAGenerator:
    """BGA package generator with parametric ball mapping."""

    def __init__(self, substrate_size: tuple[float, float]) -> None:
        self.substrate_size = substrate_size

    def generate(self, params: ParameterSet) -> Shape:
        """Generate BGA shape from parameter set."""
        return self._create_substrate(params)

# Bad
class BGAGenerator:
    def __init__(self,substrate_size):  # Missing type hints
        self.substrate_size=substrate_size  # No spaces around =

    def generate(self,params):  # Missing space after comma
        return self._create_substrate(params)  # Missing docstring
```

### Type Hints (항상 사용!)

```python
from typing import Any, Optional

def process_parameters(
    params: dict[str, Any],
    *,
    validate: bool = True,
    timeout: Optional[float] = None,
) -> ParameterSet:
    """Process and validate parameters."""
    ...
```

### Docstring (Google Style)

```python
def export_step(shape: Shape, path: str, *, metadata: dict[str, Any]) -> None:
    """Export shape to STEP file format.

    Args:
        shape: CAD shape to export.
        path: Output file path.
        metadata: Additional metadata (author, description, etc.).

    Raises:
        ValueError: If shape is invalid.
        IOError: If file cannot be written.

    Example:
        >>> shape = generator.generate(params)
        >>> export_step(shape, "output.step", metadata={"author": "John"})
    """
    ...
```

---

## 커밋 메시지 규칙

[Conventional Commits](https://www.conventionalcommits.org/) 규칙을 따릅니다.

### 형식

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type

- `feat`: 새 기능
- `fix`: 버그 수정
- `docs`: 문서 변경
- `style`: 코드 포맷 (기능 변경 없음)
- `refactor`: 리팩토링
- `perf`: 성능 개선
- `test`: 테스트 추가/수정
- `chore`: 빌드/설정 변경

### 예제

```bash
# Feature
git commit -m "feat(bga): add ball map generator with custom patterns"

# Bug fix
git commit -m "fix(export): handle invalid STEP geometry correctly"

# Breaking change
git commit -m "feat(api)!: change parameter validation API

BREAKING CHANGE: ParameterSet.validate() now returns ValidationResult
instead of raising exceptions."
```

---

## Pull Request 프로세스

### 1. PR 생성 전 체크리스트

- [ ] 모든 테스트 통과 (`pytest tests/`)
- [ ] 코드 커버리지 80% 이상
- [ ] Type check 통과 (`mypy src/`)
- [ ] Lint 통과 (`ruff check src/`)
- [ ] 문서 업데이트 (필요 시)
- [ ] CHANGELOG.md 업데이트

### 2. PR 템플릿

```markdown
## Description
<!-- 변경사항 요약 -->

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
<!-- 어떻게 테스트했는지 설명 -->

## Checklist
- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No new warnings
```

### 3. Review 프로세스

1. CI checks 통과 대기
2. 최소 1명의 reviewer 승인 필요
3. Maintainer가 최종 approve 후 merge

---

## 테스팅

### 단위 테스트

```python
# tests/unit/test_parameters.py
import pytest
from koocad.core.parameters import FloatParameter

def test_float_parameter_validation():
    """Test float parameter with constraints."""
    param = FloatParameter(
        name="width",
        value=10.0,
        min_value=0.0,
        max_value=100.0,
    )

    assert param.value == 10.0

    with pytest.raises(ValueError):
        param.value = -1.0  # Below min

def test_float_parameter_unit_conversion():
    """Test unit conversion."""
    param = FloatParameter(name="length", value=1.0, unit="inch")
    assert param.to_mm() == pytest.approx(25.4)
```

### 통합 테스트

```python
# tests/integration/test_bga_generation.py
import pytest
from koocad.components.bga import BGAGenerator
from koocad.core.parameters import ParameterSet

@pytest.mark.integration
def test_bga_generation_end_to_end():
    """Test complete BGA generation workflow."""
    params = ParameterSet({
        "substrate_width": 12.0,
        "ball_pitch": 0.8,
        "ball_rows": 15,
    })

    generator = BGAGenerator()
    shape = generator.generate(params)

    assert shape.is_valid()
    assert shape.volume() > 0

    # Export
    shape.export_step("/tmp/test_bga.step")
```

### 테스트 실행

```bash
# 전체 테스트
pytest tests/

# 단위 테스트만
pytest tests/unit/

# Coverage report
pytest tests/ --cov=koocad --cov-report=html

# 특정 마커
pytest tests/ -m "not slow"
```

---

## 문서화

### API 문서

- 모든 public 함수/클래스에 docstring 필수
- Google style docstring 사용
- 예제 코드 포함

### 사용자 가이드

- `docs/` 디렉토리에 Markdown으로 작성
- Sphinx로 HTML 생성 (`make html`)

### 변경 로그

- `CHANGELOG.md` 업데이트
- Keep a Changelog 형식 사용

---

## 질문이나 도움이 필요하신가요?

- 💬 [Discussions](https://github.com/OWNER/KooCADImGUI/discussions)
- 🐛 [Issues](https://github.com/OWNER/KooCADImGUI/issues)
- 📧 Email: dev@koocad.com

---

**Happy Coding!** 🚀
