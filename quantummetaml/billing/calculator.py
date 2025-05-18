# quantumml/billing/calculator.py
from datetime import datetime

class DeploymentCostCalculator:
    def __init__(self):
        self.rates = {
            "quantum": 0.50,  # per second
            "classical": 0.01,  # per vCPU/hour
            "edge": 0.001  # per device/day
        }

    def calculate_cost(self, deployment_type: str, metrics: dict) -> float:
        """Calculate deployment costs in real-time"""
        if deployment_type == DeploymentType.QUANTUM_HARDWARE:
            return metrics['execution_time'] * self.rates['quantum']
        elif deployment_type == DeploymentType.MANAGED_API:
            return (metrics['vcpu_seconds'] * self.rates['classical'] / 3600) + \
                   (metrics['request_count'] * 0.001)
        elif deployment_type == DeploymentType.EDGE:
            return metrics['device_count'] * self.rates['edge']
        return 0.0

    def generate_invoice(self, deployment_id: str):
        """Generate PDF invoice with quantum-safe signature"""
        # Implementation using ReportLab with quantum-resistant PDF signing