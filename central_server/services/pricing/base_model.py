# quantummetaml/core/pricing/base_model.py
class PricingStrategy(ABC):
    @abstractmethod
    def calculate_cost(self, usage_data: dict) -> float:
        pass

class TimeBasedPricing(PricingStrategy):
    def __init__(self, config_path='config/pricing/time_based.yaml'):
        self.load_config(config_path)
    
    def calculate_cost(self, usage_data):
        return (usage_data['qpu_hours'] * self.rates['quantum'] +
                usage_data['cpu_hours'] * self.rates['classical'])