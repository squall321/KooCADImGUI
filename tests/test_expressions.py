"""
Pytest test suite for KooCAD expression engine.

Advanced tests for expression evaluation and dependency resolution.
"""

import pytest
from koocad.core.expressions import ExpressionEngine


class TestExpressionEngineAdvanced:
    """Test advanced expression engine features."""

    def test_complex_expressions(self):
        """Test complex mathematical expressions."""
        engine = ExpressionEngine()
        context = {'x': 3.0, 'y': 4.0, 'z': 5.0}
        
        # Pythagorean theorem
        result = engine.evaluate('sqrt(x**2 + y**2)', context)
        assert result == 5.0
        
        # Nested functions
        result2 = engine.evaluate('max(min(x, y), z)', context)
        assert result2 == 5.0
        
        # Complex arithmetic
        result3 = engine.evaluate('(x + y) * z / 2', context)
        assert result3 == 17.5

    def test_trigonometric_functions(self):
        """Test trigonometric functions."""
        engine = ExpressionEngine()
        context = {}
        
        # sin(pi/2) = 1
        result = engine.evaluate('sin(pi/2)', context)
        assert abs(result - 1.0) < 0.0001
        
        # cos(pi) = -1
        result2 = engine.evaluate('cos(pi)', context)
        assert abs(result2 - (-1.0)) < 0.0001

    def test_exponential_and_logarithm(self):
        """Test exponential and logarithm functions."""
        engine = ExpressionEngine()
        context = {'x': 2.0}
        
        # exp(log(x)) = x
        result = engine.evaluate('exp(log(x))', context)
        assert abs(result - 2.0) < 0.0001
        
        # log(e) = 1
        result2 = engine.evaluate('log(e)', context)
        assert abs(result2 - 1.0) < 0.0001

    def test_floor_function(self):
        """Test floor function."""
        engine = ExpressionEngine()
        context = {'x': 3.7}
        
        result_floor = engine.evaluate('floor(x)', context)
        assert result_floor == 3.0

    def test_absolute_value(self):
        """Test absolute value function."""
        engine = ExpressionEngine()
        context = {'x': -5.0, 'y': 5.0}
        
        result1 = engine.evaluate('abs(x)', context)
        assert result1 == 5.0
        
        result2 = engine.evaluate('abs(y)', context)
        assert result2 == 5.0

    def test_min_max_functions(self):
        """Test min and max with multiple arguments."""
        engine = ExpressionEngine()
        context = {'a': 10.0, 'b': 5.0, 'c': 15.0, 'd': 3.0}
        
        result_max = engine.evaluate('max(a, b, c, d)', context)
        assert result_max == 15.0
        
        result_min = engine.evaluate('min(a, b, c, d)', context)
        assert result_min == 3.0

    def test_variable_extraction(self):
        """Test extracting variables from complex expressions."""
        engine = ExpressionEngine()
        
        # Simple expression
        vars1 = engine.extract_variables('x + y')
        assert vars1 == {'x', 'y'}
        
        # Complex expression
        vars2 = engine.extract_variables('sqrt(a**2 + b**2) / c')
        assert vars2 == {'a', 'b', 'c'}
        
        # With functions and constants
        vars3 = engine.extract_variables('sin(theta) + cos(phi)')
        assert vars3 == {'theta', 'phi'}

    def test_expression_with_no_variables(self):
        """Test expression with only constants."""
        engine = ExpressionEngine()
        
        result = engine.evaluate('pi * 2', {})
        assert abs(result - 6.283185) < 0.0001
        
        result2 = engine.evaluate('e ** 1', {})
        assert abs(result2 - 2.718282) < 0.0001

    def test_power_operations(self):
        """Test power operations."""
        engine = ExpressionEngine()
        context = {'x': 2.0, 'y': 3.0}
        
        result = engine.evaluate('x**y', context)
        assert result == 8.0

    def test_nested_functions(self):
        """Test nested function calls."""
        engine = ExpressionEngine()
        context = {'a': 4.0, 'b': 9.0}
        
        result = engine.evaluate('sqrt(sqrt(a))', context)
        assert abs(result - 1.414213) < 0.0001
        
        result2 = engine.evaluate('max(sqrt(a), sqrt(b))', context)
        assert result2 == 3.0


class TestExpressionErrors:
    """Test expression error handling."""

    def test_invalid_expression(self):
        """Test invalid expression raises error."""
        engine = ExpressionEngine()
        
        with pytest.raises(ValueError):
            engine.evaluate('invalid syntax!!!', {})


class TestExpressionParse:
    """Test expression parsing."""

    def test_parse_simple_expression(self):
        """Test parsing simple expression."""
        engine = ExpressionEngine()
        
        expr = engine.parse('x + y')
        assert expr is not None

    def test_parse_complex_expression(self):
        """Test parsing complex expression."""
        engine = ExpressionEngine()
        
        expr = engine.parse('sqrt(a**2 + b**2)')
        assert expr is not None

    def test_parse_with_functions(self):
        """Test parsing expression with functions."""
        engine = ExpressionEngine()
        
        expr = engine.parse('sin(x) + cos(y)')
        assert expr is not None


# Run tests with pytest
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
