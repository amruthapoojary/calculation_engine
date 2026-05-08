"""
engine/calculator.py
Formula evaluation engine - evaluates all calculations based on config.yaml
"""
import re
from typing import Dict, Any, Tuple


class FormulaEvaluator:
    """
    Evaluates mathematical formulas defined in config.yaml.
    Formulas use input metrics like I_R, I_Y, I_B, voltage, power_factor.
    """
    
    @staticmethod
    def evaluate(formula: str, metrics: Dict[str, float]) -> float:
        """
        Safely evaluate a formula string using provided metrics.
        
        Args:
            formula: Formula string like "abs(I_R - I_Y) / ((I_R + I_Y + I_B) / 3) * 100"
            metrics: Dict of metric values like {"I_R": 15.5, "I_Y": 14.2, ...}
        
        Returns:
            Calculated result as float
        
        Raises:
            ValueError: If formula contains invalid operations or references unknown metrics
        """
        # Create safe namespace with only allowed functions
        allowed_funcs = {
            'abs': abs,
            'max': max,
            'min': min,
            'round': round,
            'sum': sum,
        }
        
        # Create evaluation namespace
        namespace = {**metrics, **allowed_funcs}
        
        # Validate formula contains only safe characters
        if not re.match(r'^[a-zA-Z0-9_\s\+\-\*/().,]*$', formula):
            raise ValueError(f"Formula contains invalid characters: {formula}")
        
        try:
            result = eval(formula, {"__builtins__": {}}, namespace)
            return float(result)
        except Exception as e:
            raise ValueError(f"Error evaluating formula '{formula}': {str(e)}")
    
    @staticmethod
    def validate_formula(formula: str, available_metrics: list) -> Tuple[bool, str]:
        """
        Validate that a formula references only available metrics.
        
        Args:
            formula: Formula string to validate
            available_metrics: List of available metric names
        
        Returns:
            Tuple (is_valid: bool, message: str)
        """
        # Extract variable names from formula
        variables = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', formula)
        
        allowed_funcs = {'abs', 'max', 'min', 'round', 'sum'}
        unknown = set(variables) - set(available_metrics) - allowed_funcs
        
        if unknown:
            return False, f"Unknown metrics/functions: {unknown}"
        
        return True, "Formula is valid"


class AlertEvaluator:
    """
    Evaluates alert status based on thresholds defined in config.yaml.
    """
    
    @staticmethod
    def evaluate_status(value: float, thresholds: Dict[str, float]) -> str:
        """
        Determine alert status based on value and thresholds.
        
        Args:
            value: Calculated metric value
            thresholds: Dict with keys "alert", "warning", "alarm"
                       e.g., {"alert": 5, "warning": 10, "alarm": 20}
        
        Returns:
            Status string: "NORMAL", "ALERT", "WARNING", or "ALARM"
        """
        alarm = thresholds.get("alarm", float('inf'))
        warning = thresholds.get("warning", float('inf'))
        alert = thresholds.get("alert", float('inf'))
        
        if value > alarm:
            return "ALARM"
        elif value > warning:
            return "WARNING"
        elif value > alert:
            return "ALERT"
        else:
            return "NORMAL"
    
    @staticmethod
    def get_worst_status(*statuses: str) -> str:
        """
        Get the worst (highest priority) status from multiple statuses.
        Priority: ALARM > WARNING > ALERT > NORMAL
        """
        priority = {"ALARM": 4, "WARNING": 3, "ALERT": 2, "NORMAL": 1}
        return max(statuses, key=lambda s: priority.get(s, 0))


class CalculationEngine:
    """
    Main calculation engine that coordinates formula evaluation and alerts.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize engine with configuration.
        
        Args:
            config: Configuration dict from config.yaml
        """
        self.config = config
        self.calculations = config.get("calculations", {})
        self.alerts = config.get("alerts", {})
        self.asset = config.get("asset", {})
    
    def calculate_all_metrics(self, input_metrics: Dict[str, float]) -> Dict[str, Any]:
        """
        Calculate all metrics for given input data.
        
        Args:
            input_metrics: Raw input from Kafka (I_R, I_Y, I_B, voltage, power_factor)
        
        Returns:
            Dict with all calculated metrics and their values
        """
        results = {}
        
        for metric_name, calc_config in self.calculations.items():
            formula = calc_config["formula"]
            unit = calc_config.get("unit", "")
            precision = calc_config.get("precision", 2)
            display_name = calc_config.get("display_name", metric_name)
            
            try:
                value = FormulaEvaluator.evaluate(formula, input_metrics)
                value = round(value, precision)
                
                results[metric_name] = {
                    "value": value,
                    "unit": unit,
                    "display_name": display_name,
                    "formula": formula,
                }
            except ValueError as e:
                results[metric_name] = {
                    "value": None,
                    "error": str(e),
                    "unit": unit,
                    "display_name": display_name,
                }
        
        return results
    
    def evaluate_all_alerts(self, calculated_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate alert status for all calculated metrics.
        
        Args:
            calculated_metrics: Output from calculate_all_metrics()
        
        Returns:
            Dict with alert status for each metric
        """
        alert_results = {}
        
        for metric_name, metric_data in calculated_metrics.items():
            if "error" in metric_data or metric_data["value"] is None:
                alert_results[metric_name] = {
                    "status": "UNKNOWN",
                    "value": metric_data.get("value"),
                    "reason": "Calculation error",
                }
                continue
            
            value = metric_data["value"]
            
            # Get thresholds for this metric if they exist
            if metric_name in self.alerts:
                thresholds = self.alerts[metric_name]
                status = AlertEvaluator.evaluate_status(value, thresholds)
                
                alert_results[metric_name] = {
                    "status": status,
                    "value": value,
                    "unit": metric_data.get("unit"),
                    "thresholds": thresholds,
                    "status_description": thresholds.get("status_map", {}).get(status, ""),
                }
            else:
                # Metric has no alert thresholds defined
                alert_results[metric_name] = {
                    "status": "N/A",
                    "value": value,
                    "reason": "No thresholds configured",
                }
        
        return alert_results
    
    def process(self, input_metrics: Dict[str, float]) -> Dict[str, Any]:
        """
        Full processing pipeline: calculate metrics, evaluate alerts, determine worst status.
        
        Args:
            input_metrics: Raw input from Kafka
        
        Returns:
            Dict with complete results including all metrics, alerts, and worst status
        """
        calculated = self.calculate_all_metrics(input_metrics)
        alerts = self.evaluate_all_alerts(calculated)
        
        # Determine worst alert status
        statuses = [alert["status"] for alert in alerts.values() if alert["status"] != "N/A"]
        worst_status = AlertEvaluator.get_worst_status(*statuses) if statuses else "NORMAL"
        
        return {
            "asset_id": self.asset.get("id", "unknown"),
            "asset_name": self.asset.get("name", "unknown"),
            "input_metrics": input_metrics,
            "metrics": calculated,
            "alerts": alerts,
            "worst_status": worst_status,
        }
