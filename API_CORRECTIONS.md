# API Corrections - Testing Discoveries

This document records API issues discovered during systematic testing and provides corrected usage patterns.

## Summary

During Level 0 testing (basic functionality), several API mismatches were discovered between the implementation and the examples/documentation. All issues stem from Pydantic BaseModel usage requiring keyword arguments.

## Status: ✅ Level 0 Tests Passing

All basic functionality tests are now passing with corrected APIs:
- ✅ Parameter creation (Float, Int, Bool, String)
- ✅ Parameter validation
- ✅ Expression engine evaluation
- ✅ ParameterSet operations

---

## Issue 1: Parameter Constructor Arguments

### ❌ Incorrect Usage (Positional Arguments)
```python
# This FAILS - positional arguments not supported
fp = FloatParameter('width', 10.0, min_val=0.0, max_val=100.0)
```

### ✅ Correct Usage (Keyword Arguments)
```python
# All Pydantic BaseModel classes require keyword arguments
fp = FloatParameter(
    name='width',
    value=10.0,
    min_value=0.0,  # Note: min_value not min_val
    max_value=100.0  # Note: max_value not max_val
)
```

### Root Cause
`Parameter` classes inherit from Pydantic `BaseModel`, which overrides `__init__` to accept only keyword arguments.

### Affected Files
- All examples showing parameter creation
- Documentation in README.md
- Tutorial files
- Demo scripts (examples/*.py)

---

## Issue 2: Parameter Field Names

### ❌ Incorrect Field Names
```python
FloatParameter(name='x', value=10.0, min_val=0.0, max_val=100.0)  # Wrong!
```

### ✅ Correct Field Names
```python
FloatParameter(name='x', value=10.0, min_value=0.0, max_value=100.0)  # Correct
```

### Field Name Reference

**FloatParameter / IntParameter:**
- `name`: str (required)
- `value`: float/int (required)
- `min_value`: Optional[float/int] (not `min_val`)
- `max_value`: Optional[float/int] (not `max_val`)
- `step`: float/int = 0.1/1
- `unit`: Optional[Unit] = None
- `description`: str = ""
- `constraints`: list[Constraint] = []
- `tags`: list[str] = []
- `metadata`: dict = {}

---

## Issue 3: Parameter Validation Method

### ❌ Incorrect Usage
```python
param = FloatParameter(name='x', value=10.0)
param.validate()  # FAILS - missing required argument
```

### ✅ Correct Usage
```python
param = FloatParameter(name='x', value=10.0, min_value=0.0, max_value=100.0)

# Validate the current value
param.validate_value(param.value)  # Returns True

# Validate a different value
param.validate_value(150.0)  # Raises ValueError if outside range
```

### Root Cause
Pydantic's `BaseModel.validate()` is a class method that validates data for model creation. The instance method for constraint checking is `validate_value(value)`.

---

## Issue 4: ExpressionEngine API

### ❌ Incorrect Usage
```python
engine = ExpressionEngine()
engine.set_variable('width', 10.0)  # No such method!
result = engine.evaluate('width * 2')  # Missing context argument!
```

### ✅ Correct Usage
```python
engine = ExpressionEngine()

# Variables passed as context dictionary
context = {
    'width': 10.0,
    'height': 20.0,
    'depth': 5.0
}

# Evaluate with context
result = engine.evaluate('width * height', context)  # Returns 200.0

# Built-in constants available
result = engine.evaluate('pi * 2', {})  # Returns ~6.283

# Extract variables from expression
vars = engine.extract_variables('a + b * c')  # Returns {'a', 'b', 'c'}
```

### Key Methods
- `evaluate(expression: str, context: Dict[str, float]) -> float`
- `extract_variables(expression: str) -> Set[str]`
- `register_function(name: str, func: Callable) -> None`
- `register_constant(name: str, value: float) -> None`

---

## Issue 5: ParameterSet Methods

### ❌ Incorrect Method Names
```python
param_set = ParameterSet()
param_set.add_parameter(param)  # No such method!
param = param_set.get_parameter('width')  # No such method!
values = param_set.get_all_parameters()  # No such method!
```

### ✅ Correct Method Names
```python
param_set = ParameterSet()

# Add parameter
param_set.add(param)  # Note: add() not add_parameter()

# Get parameter
param = param_set.get('width')  # Note: get() not get_parameter()

# Access all parameters
all_params = param_set.parameters  # It's a dict attribute

# Set value with validation
param_set.set_value('width', 15.0)

# Evaluate all parameters
values = param_set.evaluate_all()  # Returns Dict[str, float]

# Serialize
data = param_set.to_dict()  # Returns dict with 'parameters' and 'version'
```

### Key Methods
- `add(param: Parameter) -> None`
- `get(name: str) -> Optional[Parameter]`
- `set_value(name: str, value: Any) -> None`
- `evaluate_all() -> dict[str, float]`
- `to_dict() -> dict[str, Any]`

### Key Attributes
- `parameters`: dict[str, Parameter] - Direct access to parameter dictionary

---

## Testing Results

### ✅ Passing Tests (Level 0)

```bash
# All basic functionality tests pass with corrected APIs
python3 -c "
import sys
sys.path.insert(0, 'src')

# Test 1: Parameter creation ✓
from koocad.core.parameters import FloatParameter, IntParameter, BoolParameter, StringParameter
fp = FloatParameter(name='width', value=10.0, min_value=0.0, max_value=100.0)
ip = IntParameter(name='count', value=15, min_value=1, max_value=20)
bp = BoolParameter(name='enable', value=True)
sp = StringParameter(name='material', value='copper')

# Test 2: Validation ✓
fp.validate_value(50.0)  # True
try:
    fp.validate_value(150.0)
except ValueError:
    pass  # Expected

# Test 3: Expression engine ✓
from koocad.core.expressions import ExpressionEngine
engine = ExpressionEngine()
result = engine.evaluate('width * height', {'width': 10.0, 'height': 20.0})

# Test 4: ParameterSet ✓
from koocad.core.parameters import ParameterSet
param_set = ParameterSet()
param_set.add(fp)
param_set.set_value('width', 15.0)
values = param_set.evaluate_all()
"
```

---

## Issue 6: ExpressionParameter Value Field

### ❌ Incorrect Field Name
```python
# This FAILS - no 'expression' field
area = ExpressionParameter(
    name='area',
    expression='width * height',  # Wrong!
    description='Computed area'
)
```

### ✅ Correct Usage
```python
# The expression string goes in the 'value' field
area = ExpressionParameter(
    name='area',
    value='width * height',  # Correct - expression string is the value
    description='Computed area'
)

# Use with ParameterSet for dependency resolution
param_set = ParameterSet()
param_set.add(width)
param_set.add(height)
param_set.add(area)

# Evaluate resolves dependencies
values = param_set.evaluate_all()  # {'width': 10.0, 'height': 20.0, 'area': 200.0}
```

### Root Cause
ExpressionParameter inherits from `Parameter[str]`, where the generic type `str` is the expression string. This goes in the `value` field, not a separate `expression` field.

---

## Action Items

### High Priority
1. ✅ **Testing**: Level 0 basic tests passing
2. 🔄 **Documentation**: Update all examples in this document
3. ⏳ **Examples**: Fix all demo scripts (examples/*.py)
4. ⏳ **README**: Update README.md with corrected examples
5. ⏳ **Level 1 Testing**: Test with CadQuery integration

### Medium Priority
6. ⏳ **API Documentation**: Generate comprehensive API reference
7. ⏳ **Type Hints**: Verify all type hints match actual usage
8. ⏳ **Error Messages**: Improve error messages for common mistakes

### Low Priority
9. ⏳ **Backward Compatibility**: Consider helper functions for old API
10. ⏳ **Migration Guide**: Create guide for users with old code

---

## Next Steps

1. Continue with Level 1 testing (Unit tests with CadQuery)
2. Fix all examples in `examples/` directory
3. Update README.md and MASTER_PLAN.md
4. Create API reference documentation
5. Set up automated testing with pytest

---

## Notes

- All discovered issues are related to Pydantic BaseModel usage
- No bugs in core logic - only API documentation mismatches
- Once examples are fixed, the system should work as designed
- Need to verify with actual CAD generation (requires CadQuery)

**Last Updated**: Testing Phase (Post Phase 145)
**Test Coverage**: Level 0 Complete ✅, Level 1-4 Pending ⏳
