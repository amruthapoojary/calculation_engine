"""
test_calculator.py
Unit tests for the calculation engine.
Run with: pytest test_calculator.py
"""
import pytest
from engine.calculator import FormulaEvaluator, AlertEvaluator, CalculationEngine
import yaml


def test_formula_evaluator_simple():
    """Test basic arithmetic evaluation."""
    result = FormulaEvaluator.evaluate("2 + 3 * 4", {})
    assert result == 14  # 2 + (3*4) = 14


def test_formula_evaluator_with_variables():
    """Test formula with input variables."""
    metrics = {"I_R": 15.5, "I_Y": 14.2, "I_B": 16.1}
    result = FormulaEvaluator.evaluate(
        "abs(I_R - I_Y) / ((I_R + I_Y + I_B) / 3) * 100",
        metrics
    )
    assert 8 < result < 9  # ~8.51%


def test_formula_evaluator_functions():
    """Test supported functions."""
    metrics = {"I_R": 15, "I_Y": 14, "I_B": 16}
    
    # Test max
    result = FormulaEvaluator.evaluate("max(I_R, I_Y, I_B)", metrics)
    assert result == 16
    
    # Test min
    result = FormulaEvaluator.evaluate("min(I_R, I_Y, I_B)", metrics)
    assert result == 14
    
    # Test sum
    result = FormulaEvaluator.evaluate("sum([I_R, I_Y, I_B])", metrics)
    assert result == 45


def test_formula_validation():
    """Test formula validation."""
    # Valid formula
    is_valid, msg = FormulaEvaluator.validate_formula(
        "I_R + I_Y - I_B",
        ["I_R", "I_Y", "I_B"]
    )
    assert is_valid
    
    # Invalid formula (unknown variable)
    is_valid, msg = FormulaEvaluator.validate_formula(
        "I_R + UNKNOWN",
        ["I_R", "I_Y", "I_B"]
    )
    assert not is_valid


def test_alert_evaluator_normal():
    """Test alert status evaluation - normal case."""
    thresholds = {"alert": 5, "warning": 10, "alarm": 20}
    status = AlertEvaluator.evaluate_status(3.2, thresholds)
    assert status == "NORMAL"


def test_alert_evaluator_alert():
    """Test alert status evaluation - alert level."""
    thresholds = {"alert": 5, "warning": 10, "alarm": 20}
    status = AlertEvaluator.evaluate_status(7.5, thresholds)
    assert status == "ALERT"


def test_alert_evaluator_warning():
    """Test alert status evaluation - warning level."""
    thresholds = {"alert": 5, "warning": 10, "alarm": 20}
    status = AlertEvaluator.evaluate_status(15.0, thresholds)
    assert status == "WARNING"


def test_alert_evaluator_alarm():
    """Test alert status evaluation - alarm level."""
    thresholds = {"alert": 5, "warning": 10, "alarm": 20}
    status = AlertEvaluator.evaluate_status(25.0, thresholds)
    assert status == "ALARM"


def test_alert_evaluator_worst_status():
    """Test worst status determination."""
    status = AlertEvaluator.get_worst_status("NORMAL", "ALERT", "NORMAL")
    assert status == "ALERT"
    
    status = AlertEvaluator.get_worst_status("WARNING", "ALERT", "ALARM")
    assert status == "ALARM"


def test_calculation_engine_process():
    """Test complete calculation engine processing."""
    config = {
        "asset": {"id": "motor1", "name": "Motor 1"},
        "calculations": {
            "imbalance": {
                "formula": "abs(I_R - I_Y) / ((I_R + I_Y + I_B) / 3) * 100",
                "unit": "%",
                "precision": 2,
                "display_name": "Imbalance",
            },
            "power": {
                "formula": "voltage * ((I_R + I_Y + I_B) / 3) * power_factor * 1.732",
                "unit": "W",
                "precision": 1,
                "display_name": "Power",
            },
        },
        "alerts": {
            "imbalance": {"alert": 5, "warning": 10, "alarm": 20},
            "power": {"alert": 5000, "warning": 8000, "alarm": 10000},
        },
    }
    
    engine = CalculationEngine(config)
    
    input_metrics = {
        "I_R": 15.5,
        "I_Y": 14.2,
        "I_B": 16.1,
        "voltage": 415.0,
        "power_factor": 0.95,
    }
    
    result = engine.process(input_metrics)
    
    # Check structure
    assert "asset_id" in result
    assert "metrics" in result
    assert "alerts" in result
    assert "worst_status" in result
    
    # Check values
    assert result["asset_id"] == "motor1"
    assert "imbalance" in result["metrics"]
    assert "power" in result["metrics"]
    
    # Check alert evaluation
    assert result["alerts"]["imbalance"]["status"] == "NORMAL"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
