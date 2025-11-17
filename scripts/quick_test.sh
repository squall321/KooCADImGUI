#!/bin/bash
# KooCAD 빠른 테스트 스크립트
# Ubuntu 환경에서 핵심 기능을 빠르게 검증합니다.

set -e  # 에러 시 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 함수 정의
print_header() {
    echo ""
    echo "======================================================================"
    echo "$1"
    echo "======================================================================"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 시작
print_header "KooCAD Ubuntu 빠른 테스트"
echo "테스트 시작 시간: $(date)"
echo ""

# Level 0: Python 환경 확인
print_header "Level 0: Python 환경 확인"

if command -v python3.11 &> /dev/null; then
    PYTHON_VERSION=$(python3.11 --version)
    print_success "Python 설치 확인: $PYTHON_VERSION"
    PYTHON_CMD="python3.11"
elif command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    if [[ $PYTHON_VERSION == *"3.11"* ]] || [[ $PYTHON_VERSION == *"3.12"* ]]; then
        print_success "Python 설치 확인: $PYTHON_VERSION"
        PYTHON_CMD="python3"
    else
        print_error "Python 3.11+ 필요. 현재: $PYTHON_VERSION"
        exit 1
    fi
else
    print_error "Python 3.11+ 설치 필요"
    echo "설치 방법: sudo apt install python3.11"
    exit 1
fi

# 가상환경 확인
if [[ -z "$VIRTUAL_ENV" ]] && [[ -z "$CONDA_DEFAULT_ENV" ]]; then
    print_warning "가상환경이 활성화되지 않음"
    echo "권장: python3.11 -m venv venv && source venv/bin/activate"
    read -p "계속하시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    print_success "가상환경 활성화됨: ${VIRTUAL_ENV:-$CONDA_DEFAULT_ENV}"
fi

# PYTHONPATH 설정
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
print_success "PYTHONPATH 설정: $(pwd)/src"

# Level 1: 핵심 의존성 확인
print_header "Level 1: 핵심 의존성 설치 및 확인"

PACKAGES=("pydantic>=2.6.0" "sympy>=1.12" "numpy>=1.26.0" "pytest>=8.0.0" "pytest-cov>=4.1.0")

print_success "필수 패키지 설치 중..."
pip install -q "${PACKAGES[@]}" 2>&1 | grep -v "Requirement already satisfied" || true

# 설치 확인
$PYTHON_CMD << 'EOF'
import sys

packages = [
    ('pydantic', 'Pydantic'),
    ('sympy', 'SymPy'),
    ('numpy', 'NumPy'),
    ('pytest', 'Pytest'),
]

print("\n패키지 버전 확인:")
for module, name in packages:
    try:
        mod = __import__(module)
        version = getattr(mod, '__version__', 'unknown')
        print(f"  ✅ {name:12s}: {version}")
    except ImportError:
        print(f"  ❌ {name:12s}: 미설치")
        sys.exit(1)
EOF

if [ $? -eq 0 ]; then
    print_success "모든 핵심 패키지 설치 확인"
else
    print_error "패키지 설치 실패"
    exit 1
fi

# Level 1: 모듈 Import 테스트
print_header "Level 1: KooCAD 모듈 Import 테스트"

$PYTHON_CMD << 'EOF'
import sys
sys.path.insert(0, 'src')

modules = [
    'koocad.core.parameters',
    'koocad.core.expressions',
    'koocad.core.presets',
    'koocad.core.validation',
    'koocad.core.serialization',
]

print("\nKooCAD 모듈 로딩:")
failed = 0
for mod in modules:
    try:
        __import__(mod)
        print(f"  ✅ {mod}")
    except Exception as e:
        print(f"  ❌ {mod}: {e}")
        failed += 1

if failed > 0:
    print(f"\n에러: {failed}개 모듈 로딩 실패")
    sys.exit(1)
else:
    print("\n모든 모듈 로딩 성공!")
EOF

if [ $? -ne 0 ]; then
    print_error "모듈 Import 실패"
    exit 1
fi

print_success "모든 모듈 Import 성공"

# Level 1: Pytest 실행
print_header "Level 1: 단위 테스트 실행 (pytest)"

if pytest tests/ -v --tb=short > /tmp/pytest_output.txt 2>&1; then
    PASSED=$(grep -o "[0-9]* passed" /tmp/pytest_output.txt | awk '{print $1}')
    print_success "Pytest 완료: $PASSED 테스트 통과"

    # 주요 결과만 출력
    echo ""
    echo "테스트 결과 요약:"
    tail -10 /tmp/pytest_output.txt
else
    print_error "일부 테스트 실패"
    echo ""
    echo "에러 내용:"
    cat /tmp/pytest_output.txt
    exit 1
fi

# Level 2: CadQuery 확인 (선택)
print_header "Level 2: CadQuery 확인 (선택)"

if $PYTHON_CMD -c "import cadquery" 2>/dev/null; then
    CQ_VERSION=$($PYTHON_CMD -c "import cadquery as cq; print(cq.__version__)")
    print_success "CadQuery 설치됨: $CQ_VERSION"

    # 간단한 CAD 생성 테스트
    print_success "간단한 3D 모델 생성 테스트 중..."
    mkdir -p output/quick_test

    $PYTHON_CMD << 'EOF'
import sys
sys.path.insert(0, 'src')
import cadquery as cq
from koocad.core.presets import BGAPresets

# BGA 프리셋 로드
presets = BGAPresets.get_all()
bga = presets['BGA_15x15_0.8mm']
values = bga.evaluate_all()

# 간단한 기판 생성
substrate = cq.Workplane("XY").box(
    values['substrate_width'],
    values['substrate_height'],
    values['substrate_thickness']
)

# STEP 파일 저장
cq.exporters.export(substrate, "output/quick_test/test_substrate.step")
print(f"✅ STEP 파일 생성: output/quick_test/test_substrate.step")
print(f"   크기: {values['substrate_width']}mm x {values['substrate_height']}mm x {values['substrate_thickness']}mm")
EOF

    if [ $? -eq 0 ] && [ -f "output/quick_test/test_substrate.step" ]; then
        FILE_SIZE=$(ls -lh output/quick_test/test_substrate.step | awk '{print $5}')
        print_success "CAD 생성 성공 (파일 크기: $FILE_SIZE)"
    else
        print_error "CAD 생성 실패"
    fi
else
    print_warning "CadQuery 미설치 (실제 CAD 생성 불가)"
    echo "설치 방법: conda install -c conda-forge cadquery"
    echo "또는: pip install cadquery"
fi

# 최종 요약
print_header "테스트 완료 요약"

echo "테스트 완료 시간: $(date)"
echo ""
echo "✅ 완료된 항목:"
echo "  - Python 3.11+ 환경 확인"
echo "  - 핵심 패키지 설치 (Pydantic, SymPy, NumPy)"
echo "  - KooCAD 모듈 Import"
echo "  - 단위 테스트 ($PASSED 테스트 통과)"

if $PYTHON_CMD -c "import cadquery" 2>/dev/null; then
    echo "  - CadQuery 설치 및 CAD 생성"
else
    echo ""
    echo "⚠️  선택 항목:"
    echo "  - CadQuery 미설치 (Level 2 테스트 필요 시 설치)"
fi

echo ""
echo "======================================================================"
echo "🎉 KooCAD 핵심 기능 테스트 성공!"
echo "======================================================================"
echo ""
echo "다음 단계:"
echo "  1. CadQuery 설치: conda install -c conda-forge cadquery"
echo "  2. Backend 테스트: docker-compose up -d"
echo "  3. 전체 테스트: 문서 참조 (UBUNTU_TEST_PLAN.md)"
echo ""

exit 0
